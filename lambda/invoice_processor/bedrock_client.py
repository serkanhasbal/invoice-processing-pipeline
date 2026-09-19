"""
Bedrock Client
--------------
WHAT IT IS:
  A helper module that calls Amazon Bedrock to extract structured invoice
  data from a raw invoice file (PDF, JPG, JPEG, or PNG).

WHY IT EXISTS:
  Bedrock is the AI layer of the pipeline. It reads the invoice image or
  PDF and returns structured JSON containing all the invoice fields we
  care about (vendor name, amounts, dates, line items, etc.).

LAYER: Application code (runs inside AWS Lambda at runtime)

HOW IT CONNECTS:
  - handler.py calls extract_invoice_data() with the raw file bytes,
    the file extension, and the AppConfig configuration dict.
  - The model ID, temperature, and max_tokens all come from AppConfig.

APPROACH — Bedrock Converse API:
  We use boto3's bedrock-runtime converse() method instead of invoke_model().

  Why converse() instead of invoke_model()?
    invoke_model() requires the entire request body to be JSON-serialised.
    This means file bytes must be base64-encoded and embedded in the JSON,
    which works in theory but boto3's json.dumps() cannot serialize raw bytes
    directly -- you would have to manually base64-encode every binary field.

    converse() is a higher-level API that accepts Python dicts with native
    bytes values. boto3 handles the serialisation internally. This is cleaner,
    less error-prone, and the recommended approach for multimodal content.

  The converse() API is compatible with Amazon Nova and Anthropic Claude models.
"""

import logging
from typing import Any

import boto3

logger = logging.getLogger(__name__)

# Supported file types and their Bedrock media type identifiers.
_MEDIA_TYPE_MAP = {
    "jpg":  ("image",    "jpeg"),
    "jpeg": ("image",    "jpeg"),
    "png":  ("image",    "png"),
    "pdf":  ("document", "pdf"),
}

_PROMPTS = {
    "v1": """You are a precise invoice data extraction assistant.

Extract all invoice information from the provided document and return it as a single valid JSON object.

Rules:
- Return ONLY the JSON object. No explanations, no markdown code blocks, no extra text.
- Use null for any field that is not present in the invoice.
- Dates must use YYYY-MM-DD format (e.g. 2024-03-15). Use null if the date cannot be determined.
- Monetary amounts must be plain numbers without currency symbols (e.g. 1250.00 not $1,250.00).
- currency must be the 3-letter ISO code (e.g. USD, EUR, GBP). Use null if unknown.
- payment_status should be one of: PAID, UNPAID, OVERDUE, or null if not mentioned.
- line_items must be a JSON array. Use an empty array [] if no line items are present.

Return exactly this structure:
{
  "invoice_id": "string or null",
  "vendor_name": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "currency": "3-letter code or null",
  "subtotal": number or null,
  "tax_amount": number or null,
  "total_amount": number or null,
  "payment_status": "PAID|UNPAID|OVERDUE or null",
  "purchase_order_number": "string or null",
  "line_items": [
    {
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "line_total": number
    }
  ]
}""",

    # v2: Significantly improved prompt.
    #
    # Key improvements over v1:
    #
    # 1. EXPLICIT field-finding guidance
    #    v1 just named fields. v2 tells the model WHERE to look on the invoice
    #    (e.g. "invoice number", "bill to", "net amount") so it doesn't miss
    #    fields that use non-standard labels.
    #
    # 2. AMOUNT HANDLING
    #    v1 said "plain numbers". v2 adds: strip commas/spaces, handle European
    #    decimal notation (1.250,00 → 1250.00), never return negative totals.
    #
    # 3. DATE HANDLING
    #    v1 said "YYYY-MM-DD". v2 adds examples of common formats to convert
    #    (e.g. "01 March 2024", "03/01/24") and explicit year-inference rules.
    #
    # 4. CURRENCY INFERENCE
    #    v1 said "3-letter code". v2 adds: infer from symbols (€→EUR, $→USD,
    #    £→GBP) and from the vendor's country if no symbol is present.
    #
    # 5. PAYMENT STATUS INFERENCE
    #    v1 required exact keywords. v2 adds inference rules: look for
    #    "Paid", "Settled", "Outstanding", "Past due", stamp marks, etc.
    #
    # 6. VENDOR NAME CLARITY
    #    v2 clarifies: use the company issuing the invoice (the seller),
    #    not the recipient. Avoids common model confusion.
    #
    # 7. LINE ITEM FALLBACK
    #    v2: if a document has no itemised lines but has a description,
    #    create a single line item from the total. Avoids empty line_items
    #    for simple one-line invoices.
    #
    # 8. CONSISTENCY RULE
    #    v2 adds: if subtotal + tax_amount can be computed and matches
    #    total_amount, use those values. If only total is present, set
    #    subtotal = total and tax_amount = 0.

    "v2": """You are an expert invoice data extraction system. Your only job is to read invoice documents and return structured data in valid JSON format.

## Output format

Return ONLY a single valid JSON object. No markdown, no code fences, no commentary before or after.

## Field extraction rules

**invoice_id**
Look for: Invoice Number, Invoice No, Invoice #, Facture No, Rechnung Nr, Bill Number, Reference Number.
Use the most prominent alphanumeric identifier on the document.
If multiple candidate IDs exist, prefer the one labelled "invoice".

**vendor_name**
This is the company ISSUING the invoice (the seller, not the buyer).
Look in the top section of the document, letterhead, or "From:" / "Billed by:" fields.
Use the full legal company name if visible.

**invoice_date**
Look for: Invoice Date, Date, Issued, Issue Date, Billing Date.
Convert any date format to YYYY-MM-DD (e.g. "01 March 2024" → "2024-03-01", "03/01/24" → "2024-03-01").
If year is ambiguous, prefer the most recent plausible year.

**due_date**
Look for: Due Date, Payment Due, Pay By, Terms (e.g. "Net 30" means due_date = invoice_date + 30 days).
Convert to YYYY-MM-DD. If a Net N term is given but no explicit due date, calculate from invoice_date.

**currency**
Return the 3-letter ISO code.
Infer from symbols: € → EUR, $ → USD, £ → GBP, ¥ → JPY, Fr → CHF.
If no symbol is present, infer from the vendor country or document language.
Default to null only if truly ambiguous.

**subtotal**
Look for: Subtotal, Net Amount, Net Total, Amount before tax, Nettobetrag, Montant HT.
Return as a plain decimal number (e.g. 1250.00).
Strip currency symbols, commas used as thousand separators, and spaces.
Handle European notation: "1.250,00" → 1250.00.

**tax_amount**
Look for: Tax, VAT, GST, MwSt, TVA, IVA, Sales Tax.
If multiple tax lines exist, return the total tax.
If no tax is shown, return 0.0 (not null) when a subtotal and total are both present.

**total_amount**
Look for: Total, Grand Total, Amount Due, Total Due, Gesamtbetrag, Total TTC.
This should equal subtotal + tax_amount. If the arithmetic is inconsistent, prefer the explicitly labelled total.
Never return a negative value for total_amount.

**payment_status**
Return one of: PAID, UNPAID, OVERDUE.
Infer from: "Paid" stamp, "Payment received", "Outstanding", "Past due", "Overdue", "Please pay", zero balance due.
If the document shows a balance of 0 or says "paid in full", return PAID.
If no payment information is present, return null.

**purchase_order_number**
Look for: PO Number, PO #, Purchase Order, Order Reference, Ref PO.
Return null if not present.

**line_items**
Extract every line item from the invoice table.
Each item must have: description (string), quantity (number), unit_price (number), line_total (number).
If quantity is not shown, use 1.
If unit_price is not shown but line_total is, set unit_price = line_total / quantity.
If the document has no itemised table but has a single service description, create one line item using the total_amount as line_total.
Return [] only if the document contains no extractable line information whatsoever.

## Consistency check
Before returning, verify:
- subtotal + tax_amount ≈ total_amount (allow small rounding differences)
- sum of line_item.line_total values ≈ subtotal (if line items exist)
- All amounts use the same currency

## Return this exact JSON structure
{
  "invoice_id": "string or null",
  "vendor_name": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "currency": "3-letter ISO code or null",
  "subtotal": number or null,
  "tax_amount": number or null,
  "total_amount": number or null,
  "payment_status": "PAID or UNPAID or OVERDUE or null",
  "purchase_order_number": "string or null",
  "line_items": [
    {
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "line_total": number
    }
  ]
}"""
}


def extract_invoice_data(
    file_bytes: bytes,
    file_extension: str,
    config: dict,
) -> str:
    """
    Send the invoice file to Amazon Bedrock using the Converse API
    and return the raw JSON string response.

    Parameters
    ----------
    file_bytes : bytes
        Raw bytes of the invoice file read from S3.
    file_extension : str
        File extension without the dot, lowercase: "pdf", "jpg", "jpeg", "png".
    config : dict
        Runtime configuration from AppConfig. Must contain:
          - bedrock_model_id (str)
          - temperature      (float)
          - max_tokens       (int)
          - prompt_version   (str)

    Returns
    -------
    str
        The raw text response from Bedrock. Should be a JSON string.
        invoice_parser.py is responsible for parsing and validating it.

    Raises
    ------
    ValueError
        If the file extension is not supported.
    RuntimeError
        If the Bedrock API call fails.
    """
    ext = file_extension.lower().lstrip(".")

    if ext not in _MEDIA_TYPE_MAP:
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            f"Supported types: {list(_MEDIA_TYPE_MAP.keys())}"
        )

    block_type, media_subtype = _MEDIA_TYPE_MAP[ext]
    model_id       = config["bedrock_model_id"]
    temperature    = float(config.get("temperature", 0.1))
    max_tokens     = int(config.get("max_tokens", 2000))
    prompt_version = config.get("prompt_version", "v1")
    prompt_text    = _PROMPTS.get(prompt_version, _PROMPTS["v1"])

    logger.info(
        "Calling Bedrock converse: model=%s temperature=%s max_tokens=%s "
        "file_type=%s prompt_version=%s file_size=%d bytes",
        model_id, temperature, max_tokens, ext, prompt_version, len(file_bytes),
    )

    # Build the content blocks for the Converse API.
    # boto3 converse() accepts native Python bytes in the source dict —
    # no manual base64 encoding needed.
    if block_type == "image":
        file_block: dict[str, Any] = {
            "image": {
                "format": media_subtype,
                "source": {"bytes": file_bytes},
            }
        }
    else:
        # Document block for PDFs.
        file_block = {
            "document": {
                "format": media_subtype,
                "name": "invoice",
                "source": {"bytes": file_bytes},
            }
        }

    text_block: dict[str, Any] = {"text": prompt_text}

    bedrock = boto3.client("bedrock-runtime")

    try:
        response = bedrock.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [file_block, text_block],
                }
            ],
            inferenceConfig={
                "temperature": temperature,
                "maxTokens": max_tokens,
            },
        )
    except Exception as exc:
        raise RuntimeError(
            f"Bedrock converse failed for model '{model_id}': {exc}"
        ) from exc

    # The converse() response structure:
    # { "output": { "message": { "content": [ { "text": "..." } ] } } }
    try:
        raw_text = response["output"]["message"]["content"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(
            f"Unexpected Bedrock response structure: {response}"
        ) from exc

    logger.info("Bedrock response received: %d characters", len(raw_text))
    return raw_text
