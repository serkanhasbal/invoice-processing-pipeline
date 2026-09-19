"""
Lambda Handler — Invoice Processor
------------------------------------
WHAT IT IS:
  The entry point for the invoice processor Lambda function.
  AWS calls lambda_handler() every time an invoice is uploaded to S3.

WHY IT EXISTS:
  This is the orchestrator. It reads the S3 event, calls each helper
  module in sequence, and writes the result. The goal is that this file
  reads like a clear story of what happens at each step.

LAYER: Application code (runs inside AWS Lambda at runtime)

FULL FLOW:
  1. S3 fires an event when raw/invoices/<file> is created
  2. AWS calls lambda_handler(event, context)
  3. Handler extracts bucket + key from the event
  4. Handler reads the raw invoice bytes from S3
  5. Handler fetches runtime config from AppConfig
  6. Handler sends file + prompt to Bedrock
  7. Handler parses and validates the Bedrock response
  8. Handler writes the cleaned JSON result to processed/invoices/
  9. Handler returns a summary response

PHASE 2 IMPROVEMENTS:
  - Structured per-step timing so you can see in CloudWatch how long
    each stage (S3 read, AppConfig, Bedrock, parse, S3 write) takes.
  - Processing summary metadata added to every output record:
      pipeline_version, processing_duration_ms, bedrock_model_used
  - Bedrock raw response optionally logged (controlled by AppConfig
    feature flag log_raw_bedrock_response) for debugging.
  - URL percent-decoding for S3 keys with special characters.
  - Config is fetched once per Lambda invocation and reused across
    all records in the same event batch.

ERROR HANDLING:
  Each step fails loudly: exceptions are logged with full traceback
  and re-raised. Lambda marks the invocation as failed, making it
  visible in CloudWatch. There is no silent failure.
"""

import json
import logging
import os
import time
import urllib.parse
from datetime import datetime, timezone

import boto3

import appconfig_client
import bedrock_client
import invoice_parser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_s3 = boto3.client("s3")

# Pipeline version tag — increment when making breaking changes to the
# output format so you can filter records by version in Athena.
_PIPELINE_VERSION = "2.0"


def lambda_handler(event: dict, context) -> dict:
    """
    Main entry point called by AWS Lambda.

    Parameters
    ----------
    event : dict
        The S3 event payload. Contains the bucket name and the S3 key
        of the newly uploaded invoice file.
    context : LambdaContext
        Lambda runtime context (function name, timeout, request ID, etc.).
        We don't use it directly but it is required by the Lambda signature.

    Returns
    -------
    dict
        A response dict with statusCode and a body message.
        Lambda does not use this return value for S3-triggered functions,
        but returning a structured response is good practice for testing.
    """
    logger.info("Invoice processor invoked. RequestId: %s", context.aws_request_id)
    logger.debug("Event: %s", json.dumps(event))

    records = event.get("Records", [])
    if not records:
        logger.warning("Event contained no records. Nothing to process.")
        return {"statusCode": 200, "body": "No records to process"}

    # Fetch config once for the whole batch — avoids one AppConfig call per record.
    logger.info("Fetching AppConfig configuration...")
    t0 = time.monotonic()
    config = appconfig_client.get_config()
    logger.info("AppConfig fetched in %.0f ms", (time.monotonic() - t0) * 1000)

    results = []
    for record in records:
        result = _process_single_record(record, config)
        results.append(result)

    failures = [r for r in results if not r["success"]]
    if failures:
        raise RuntimeError(
            f"{len(failures)} of {len(results)} record(s) failed: "
            + str([f["error"] for f in failures])
        )

    return {
        "statusCode": 200,
        "body": f"Successfully processed {len(results)} invoice(s)",
    }


def _process_single_record(record: dict, config: dict) -> dict:
    """
    Process one S3 event record (one uploaded invoice file).

    Parameters
    ----------
    record : dict
        One entry from event["Records"].
    config : dict
        Runtime configuration already fetched from AppConfig.

    Returns
    -------
    dict with keys: success, key, output_key, duration_ms, error
    """
    invocation_start = time.monotonic()

    bucket = record["s3"]["bucket"]["name"]
    # S3 event keys are URL-encoded (spaces become +, special chars become %XX)
    raw_key = record["s3"]["object"]["key"]
    key = urllib.parse.unquote_plus(raw_key)

    logger.info("─── Processing: s3://%s/%s ───", bucket, key)

    try:
        # ── Step 1: Read invoice from S3 ────────────────────────────────────
        t = time.monotonic()
        file_bytes, file_extension = _read_invoice_from_s3(bucket, key)
        logger.info("S3 read: %.0f ms (%d bytes)", (time.monotonic() - t) * 1000, len(file_bytes))

        # ── Step 2: Call Bedrock ─────────────────────────────────────────────
        t = time.monotonic()
        raw_bedrock_response = bedrock_client.extract_invoice_data(
            file_bytes=file_bytes,
            file_extension=file_extension,
            config=config,
        )
        bedrock_ms = (time.monotonic() - t) * 1000
        logger.info("Bedrock: %.0f ms (%d chars)", bedrock_ms, len(raw_bedrock_response))

        # Optionally log the raw Bedrock response for debugging.
        # Controlled by feature flag in AppConfig to avoid noisy production logs.
        if config.get("feature_flags", {}).get("log_raw_bedrock_response", False):
            logger.info("Raw Bedrock response: %s", raw_bedrock_response)

        # ── Step 3: Parse and validate ──────────────────────────────────────
        t = time.monotonic()
        invoice_data = invoice_parser.parse_and_validate(raw_bedrock_response)
        logger.info("Parse + validate: %.0f ms", (time.monotonic() - t) * 1000)

        # ── Step 4: Add pipeline metadata ───────────────────────────────────
        total_ms = round((time.monotonic() - invocation_start) * 1000)
        invoice_data["processed_at"]          = datetime.now(timezone.utc).isoformat()
        invoice_data["source_file"]           = f"s3://{bucket}/{key}"
        invoice_data["pipeline_version"]      = _PIPELINE_VERSION
        invoice_data["processing_duration_ms"] = total_ms
        invoice_data["bedrock_model_used"]    = config.get("bedrock_model_id", "unknown")

        # ── Step 5: Write to S3 ─────────────────────────────────────────────
        t = time.monotonic()
        output_key = _write_processed_invoice(bucket, invoice_data)
        logger.info("S3 write: %.0f ms → s3://%s/%s", (time.monotonic() - t) * 1000, bucket, output_key)

        logger.info(
            "✓ Done in %d ms | invoice_id=%s vendor=%s total=%s %s warnings=%d",
            total_ms,
            invoice_data.get("invoice_id"),
            invoice_data.get("vendor_name"),
            invoice_data.get("total_amount"),
            invoice_data.get("currency", ""),
            len(invoice_data.get("data_quality_warnings", [])),
        )

        return {
            "success":     True,
            "key":         key,
            "output_key":  output_key,
            "duration_ms": total_ms,
            "error":       None,
        }

    except Exception as exc:
        total_ms = round((time.monotonic() - invocation_start) * 1000)
        logger.error(
            "✗ Failed after %d ms | s3://%s/%s | %s",
            total_ms, bucket, key, exc, exc_info=True,
        )
        return {
            "success":     False,
            "key":         key,
            "output_key":  None,
            "duration_ms": total_ms,
            "error":       str(exc),
        }


def _read_invoice_from_s3(bucket: str, key: str) -> tuple[bytes, str]:
    """
    Read the invoice file from S3 and return (bytes, extension).

    Parameters
    ----------
    bucket : str
        S3 bucket name.
    key : str
        S3 object key, e.g. "raw/invoices/invoice-123.pdf"

    Returns
    -------
    tuple[bytes, str]
        The raw file bytes and the lowercase extension (e.g. "pdf", "jpg").

    Raises
    ------
    ValueError
        If the file extension is not a supported invoice format.
    """
    supported_extensions = {"pdf", "jpg", "jpeg", "png"}

    # Extract the extension from the key.
    # "raw/invoices/invoice-123.PDF" → "pdf"
    if "." not in key:
        raise ValueError(f"File has no extension: {key}")

    extension = key.rsplit(".", 1)[-1].lower()

    if extension not in supported_extensions:
        raise ValueError(
            f"Unsupported file type '{extension}' for key '{key}'. "
            f"Supported: {supported_extensions}"
        )

    logger.info("Reading s3://%s/%s (%s)", bucket, key, extension)

    response = _s3.get_object(Bucket=bucket, Key=key)
    file_bytes = response["Body"].read()

    logger.info("Read %d bytes from S3", len(file_bytes))

    return file_bytes, extension


def _write_processed_invoice(bucket: str, invoice_data: dict) -> str:
    """
    Write the processed invoice JSON to the processed/invoices/ prefix in S3.

    The output key is based on the invoice_id so files are easy to find.
    If invoice_id is null (shouldn't happen after validation, but just in case),
    we fall back to a timestamp-based name.

    Parameters
    ----------
    bucket : str
        S3 bucket name.
    invoice_data : dict
        Validated and enriched invoice data dict.

    Returns
    -------
    str
        The S3 key where the processed file was written.
    """
    processed_prefix = os.environ.get("PROCESSED_PREFIX", "processed/invoices/")

    invoice_id = invoice_data.get("invoice_id")
    if invoice_id:
        # Sanitise the invoice_id for use as a filename.
        # Replace slashes, spaces, and other unsafe characters.
        safe_id = invoice_id.replace("/", "-").replace(" ", "_")
        filename = f"{safe_id}.json"
    else:
        # Fallback: use a timestamp so we never lose data.
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"unknown_{timestamp}.json"

    output_key = f"{processed_prefix}{filename}"

    # Write as a single-line JSON record (no indentation).
    # Athena's JsonSerDe requires newline-delimited JSON (NDJSON) format:
    # each file must contain exactly one JSON object per line.
    # Pretty-printed multi-line JSON causes Athena to fail with a read error.
    body = json.dumps(invoice_data, default=str)

    _s3.put_object(
        Bucket=bucket,
        Key=output_key,
        Body=body.encode("utf-8"),
        ContentType="application/json",
    )

    logger.info("Wrote processed invoice to s3://%s/%s", bucket, output_key)

    return output_key
