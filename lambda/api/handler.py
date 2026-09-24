"""
API Lambda Handler
------------------
WHAT IT IS:
  A Lambda function that serves as the backend API for the React frontend.
  It is invoked by API Gateway and returns JSON responses.

WHY IT EXISTS:
  The React frontend runs in a browser. Browsers cannot directly call AWS
  services (S3, Athena) without credentials. This Lambda sits behind API
  Gateway and acts as a secure intermediary — the frontend calls it over
  HTTPS, it calls AWS services using its IAM role, and returns clean JSON.

ENDPOINTS:
  GET  /invoices          — list all processed invoices
  GET  /invoices/{id}     — get one invoice by invoice_number
  GET  /stats             — aggregate KPIs (total spend, avg PUE, etc.)
  POST /upload            — generate a presigned S3 URL for direct upload

LAYER: Application code (runs inside AWS Lambda at runtime)
"""

import json
import os
import boto3
import logging
from decimal import Decimal
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

s3        = boto3.client("s3")
BUCKET    = os.environ["INVOICE_BUCKET"]
RAW_PREFIX       = os.environ.get("RAW_PREFIX", "raw/invoices/")
PROCESSED_PREFIX = os.environ.get("PROCESSED_PREFIX", "processed/invoices/")


# ─────────────────────────────────────────────────────────────────────────────
# CORS headers — required so the browser accepts the response
# ─────────────────────────────────────────────────────────────────────────────
CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def _ok(body):
    return {
        "statusCode": 200,
        "headers": {**CORS, "Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }


def _err(code, message):
    return {
        "statusCode": code,
        "headers": {**CORS, "Content-Type": "application/json"},
        "body": json.dumps({"error": message}),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    method = event.get("httpMethod", "GET")
    path   = event.get("path", "/")
    params = event.get("pathParameters") or {}

    logger.info("%s %s", method, path)

    # Handle CORS preflight
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS, "body": ""}

    if path == "/invoices" and method == "GET":
        return get_invoices()

    if path.startswith("/invoices/") and method == "GET":
        invoice_id = params.get("id") or path.split("/invoices/")[1]
        return get_invoice(invoice_id)

    if path == "/stats" and method == "GET":
        return get_stats()

    if path == "/upload" and method == "POST":
        body = json.loads(event.get("body") or "{}")
        return get_upload_url(body)

    return _err(404, f"Route not found: {method} {path}")


# ─────────────────────────────────────────────────────────────────────────────
# GET /invoices — list all processed invoices
# ─────────────────────────────────────────────────────────────────────────────

def get_invoices():
    """
    List all JSON files in processed/invoices/ and return their contents.
    Each file is one invoice record.
    """
    try:
        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=BUCKET, Prefix=PROCESSED_PREFIX)

        invoices = []
        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith(".json"):
                    continue
                try:
                    resp = s3.get_object(Bucket=BUCKET, Key=key)
                    data = json.loads(resp["Body"].read())
                    invoices.append(data)
                except Exception as e:
                    logger.warning("Could not read %s: %s", key, e)

        # Sort by period descending, then invoice_date descending
        invoices.sort(
            key=lambda x: (x.get("period") or "", x.get("invoice_date") or ""),
            reverse=True,
        )

        return _ok({"invoices": invoices, "count": len(invoices)})

    except Exception as e:
        logger.error("get_invoices failed: %s", e, exc_info=True)
        return _err(500, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# GET /invoices/{id} — get single invoice
# ─────────────────────────────────────────────────────────────────────────────

def get_invoice(invoice_id: str):
    """Return a single invoice JSON by its invoice_number (= filename without .json)."""
    key = f"{PROCESSED_PREFIX}{invoice_id}.json"
    try:
        resp = s3.get_object(Bucket=BUCKET, Key=key)
        data = json.loads(resp["Body"].read())
        return _ok(data)
    except s3.exceptions.NoSuchKey:
        return _err(404, f"Invoice '{invoice_id}' not found")
    except Exception as e:
        logger.error("get_invoice failed: %s", e, exc_info=True)
        return _err(500, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# GET /stats — aggregate KPIs
# ─────────────────────────────────────────────────────────────────────────────

def get_stats():
    """
    Compute aggregate statistics across all processed invoices.
    Used by the KPI cards on the dashboard.
    """
    try:
        invoices_resp = get_invoices()
        if invoices_resp["statusCode"] != 200:
            return invoices_resp

        invoices = json.loads(invoices_resp["body"])["invoices"]

        if not invoices:
            return _ok({
                "total_invoices": 0,
                "total_spend_usd": 0,
                "avg_pue": None,
                "total_kwh": 0,
                "effective_usd_per_kwh": None,
                "vendors": [],
                "currencies": [],
                "by_vendor": [],
                "by_period": [],
                "by_currency": [],
            })

        total_spend_usd = sum(
            float(i.get("total_amount_usd") or 0) for i in invoices
        )
        total_kwh = sum(
            float(i.get("total_volume_kwh") or 0) for i in invoices
        )
        pue_values = [
            float(i["current_pue"]) for i in invoices if i.get("current_pue")
        ]
        avg_pue = round(sum(pue_values) / len(pue_values), 4) if pue_values else None
        effective_rate = round(total_spend_usd / total_kwh, 6) if total_kwh > 0 else None

        # By vendor
        vendor_map = {}
        for inv in invoices:
            v = inv.get("vendor") or "Unknown"
            if v not in vendor_map:
                vendor_map[v] = {
                    "vendor": v,
                    "invoice_count": 0,
                    "total_usd": 0,
                    "total_kwh": 0,
                    "city": inv.get("city"),
                    "country": inv.get("country"),
                    "country_code": inv.get("country_code"),
                }
            vendor_map[v]["invoice_count"] += 1
            vendor_map[v]["total_usd"]     += float(inv.get("total_amount_usd") or 0)
            vendor_map[v]["total_kwh"]     += float(inv.get("total_volume_kwh") or 0)
        by_vendor = sorted(vendor_map.values(), key=lambda x: x["total_usd"], reverse=True)

        # By period
        period_map = {}
        for inv in invoices:
            p = inv.get("period") or "Unknown"
            if p not in period_map:
                period_map[p] = {"period": p, "total_usd": 0, "invoice_count": 0}
            period_map[p]["total_usd"]     += float(inv.get("total_amount_usd") or 0)
            period_map[p]["invoice_count"] += 1
        by_period = sorted(period_map.values(), key=lambda x: x["period"])

        # By currency
        currency_map = {}
        for inv in invoices:
            c = inv.get("currency") or "Unknown"
            if c not in currency_map:
                currency_map[c] = {"currency": c, "total_usd": 0, "invoice_count": 0}
            currency_map[c]["total_usd"]     += float(inv.get("total_amount_usd") or 0)
            currency_map[c]["invoice_count"] += 1
        by_currency = sorted(currency_map.values(), key=lambda x: x["total_usd"], reverse=True)

        return _ok({
            "total_invoices":      len(invoices),
            "total_spend_usd":     round(total_spend_usd, 2),
            "avg_pue":             avg_pue,
            "total_kwh":           round(total_kwh, 2),
            "effective_usd_per_kwh": effective_rate,
            "vendors":             list(vendor_map.keys()),
            "currencies":          list(currency_map.keys()),
            "by_vendor":           by_vendor,
            "by_period":           by_period,
            "by_currency":         by_currency,
        })

    except Exception as e:
        logger.error("get_stats failed: %s", e, exc_info=True)
        return _err(500, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# POST /upload — generate presigned S3 URL
# ─────────────────────────────────────────────────────────────────────────────

def get_upload_url(body: dict):
    """
    Generate a presigned POST URL so the browser can upload directly to S3.

    WHY PRESIGNED URL:
      We don't want the API to receive the file bytes (that would mean
      uploading the file to Lambda, then Lambda re-uploading to S3 — slow
      and uses Lambda memory). Instead we give the browser a temporary
      signed URL and the browser uploads directly to S3. Lambda never
      sees the file bytes.

    Expected body: {"filename": "invoice.pdf", "content_type": "application/pdf"}
    """
    filename     = body.get("filename", "upload.pdf")
    content_type = body.get("content_type", "application/pdf")

    # Sanitise filename
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
    key = f"{RAW_PREFIX}{safe_name}"

    try:
        presigned = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket":      BUCKET,
                "Key":         key,
                "ContentType": content_type,
            },
            ExpiresIn=300,  # 5 minutes
        )
        return _ok({
            "upload_url":  presigned,
            "s3_key":      key,
            "expires_in":  300,
        })
    except Exception as e:
        logger.error("get_upload_url failed: %s", e, exc_info=True)
        return _err(500, str(e))
