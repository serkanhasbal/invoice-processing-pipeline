"""
Invoice Parser
--------------
WHAT IT IS:
  A helper module that takes the raw text response from Bedrock,
  extracts the JSON, validates its structure, and normalises field
  values into clean Python types ready to write to S3 and query in Athena.

WHY IT EXISTS:
  Bedrock is an AI model. Even with a strict prompt it can occasionally:
    - Wrap the JSON in markdown code fences (```json ... ```)
    - Return amounts as strings ("1,250.00") instead of numbers
    - Return dates in non-standard formats ("01 March 2024")
    - Return slightly inconsistent amount arithmetic
    - Return line items with missing fields

  This module is a defensive layer between the raw AI output and the
  rest of the pipeline. Every field is validated and normalised here so
  handler.py and the Athena schema always receive consistent, clean data.

PHASE 2 IMPROVEMENTS OVER PHASE 1:
  - Tries multiple date format patterns (not just YYYY-MM-DD)
  - Detects and corrects European decimal notation (1.250,00 → 1250.00)
  - Validates amount arithmetic (subtotal + tax ≈ total) and logs discrepancies
  - Caps obviously wrong values (negative amounts set to None)
  - Adds data_quality_warnings list to the output so issues are traceable
  - Partial-success: ValidationWarning for non-critical issues (logged but
    not raised), ValueError only for truly unrecoverable problems
  - Trims whitespace and normalises encoding in all string fields

LAYER: Application code (runs inside AWS Lambda at runtime)

HOW IT CONNECTS:
  - handler.py calls parse_and_validate() with the raw string from
    bedrock_client.py and gets back a clean dict ready to write to S3.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# These fields MUST be present and non-null for the record to be accepted.
# A missing required field raises ValueError and the invoice is not saved.
_REQUIRED_FIELDS = {"invoice_id", "vendor_name", "invoice_date", "total_amount"}

# All expected fields with their defaults.
# Any field not returned by Bedrock is filled in so the schema is always complete.
_FIELD_DEFAULTS: dict[str, Any] = {
    "invoice_id":            None,
    "vendor_name":           None,
    "invoice_date":          None,
    "due_date":              None,
    "currency":              None,
    "subtotal":              None,
    "tax_amount":            None,
    "total_amount":          None,
    "payment_status":        None,
    "purchase_order_number": None,
    "line_items":            [],
}

# Date formats we attempt to parse, in order of preference.
# strptime format strings: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
_DATE_FORMATS = [
    "%Y-%m-%d",    # 2024-03-15  (preferred — Athena native)
    "%d/%m/%Y",    # 15/03/2024
    "%m/%d/%Y",    # 03/15/2024
    "%d-%m-%Y",    # 15-03-2024
    "%d.%m.%Y",    # 15.03.2024  (European)
    "%B %d, %Y",   # March 15, 2024
    "%d %B %Y",    # 15 March 2024
    "%b %d, %Y",   # Mar 15, 2024
    "%d %b %Y",    # 15 Mar 2024
    "%Y/%m/%d",    # 2024/03/15
    "%d/%m/%y",    # 15/03/24
    "%m/%d/%y",    # 03/15/24
]

# How much subtotal + tax_amount can differ from total_amount before we warn.
# Small rounding differences (e.g. 0.01) are normal in invoices.
_AMOUNT_TOLERANCE = 0.10  # 10 cents


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def parse_and_validate(raw_text: str) -> dict:
    """
    Parse the raw Bedrock response into a validated, normalised invoice dict.

    Parameters
    ----------
    raw_text : str
        The raw text string returned by Bedrock. May be a bare JSON object
        or wrapped in markdown code fences.

    Returns
    -------
    dict
        Clean invoice dictionary with all expected fields present.
        Includes a ``data_quality_warnings`` list (may be empty) describing
        any non-critical issues detected during normalisation.

    Raises
    ------
    ValueError
        If no valid JSON can be extracted, or required fields are missing/null.
    """
    warnings: list[str] = []

    # ── Step 1: Extract JSON from raw text ──────────────────────────────────
    json_str = _extract_json_string(raw_text)

    # ── Step 2: Parse JSON ───────────────────────────────────────────────────
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Bedrock response is not valid JSON: {exc}\n"
            f"Raw text (first 400 chars): {raw_text[:400]}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object at the top level, got: {type(data).__name__}"
        )

    # ── Step 3: Fill missing fields with defaults ────────────────────────────
    normalised = {**_FIELD_DEFAULTS, **data}

    # ── Step 4: Normalise all field types ────────────────────────────────────
    normalised, warnings = _normalise_all_fields(normalised, warnings)

    # ── Step 5: Validate required fields ─────────────────────────────────────
    _validate_required_fields(normalised)

    # ── Step 6: Cross-field consistency checks ───────────────────────────────
    warnings = _check_amount_consistency(normalised, warnings)

    # ── Step 7: Attach quality warnings to the output ────────────────────────
    # This means every processed invoice carries a record of any issues found.
    # Great for data quality monitoring in Athena later.
    normalised["data_quality_warnings"] = warnings

    if warnings:
        logger.warning(
            "Invoice %s parsed with %d warning(s): %s",
            normalised.get("invoice_id"), len(warnings), warnings,
        )
    else:
        logger.info(
            "Invoice parsed cleanly: invoice_id=%s vendor=%s total=%s %s",
            normalised.get("invoice_id"),
            normalised.get("vendor_name"),
            normalised.get("total_amount"),
            normalised.get("currency", ""),
        )

    return normalised


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_json_string(text: str) -> str:
    """
    Extract a JSON object from text that may contain markdown or other noise.

    Strategy (in order):
      1. ```json ... ``` or ``` ... ``` markdown code fence
      2. Outermost { ... } block
      3. Full text as-is (json.loads will surface the error)
    """
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        logger.debug("Extracted JSON from markdown code fence")
        return fence.group(1).strip()

    brace = re.search(r"\{[\s\S]*\}", text)
    if brace:
        logger.debug("Extracted JSON via outermost brace matching")
        return brace.group(0).strip()

    logger.warning("Could not isolate JSON block; attempting to parse full response text")
    return text.strip()


def _validate_required_fields(data: dict) -> None:
    """Raise ValueError listing every required field that is null or missing."""
    missing = [f for f in _REQUIRED_FIELDS if data.get(f) is None]
    if missing:
        raise ValueError(
            f"Invoice missing required fields {missing}. "
            f"Available fields: { {k: v for k, v in data.items() if k != 'line_items'} }"
        )


def _normalise_all_fields(data: dict, warnings: list[str]) -> tuple[dict, list[str]]:
    """Apply type normalisation to every field."""

    # ── Numeric amount fields ─────────────────────────────────────────────────
    for field in ("subtotal", "tax_amount", "total_amount"):
        value, warn = _to_float(data[field], field)
        data[field] = value
        if warn:
            warnings.append(warn)
        # Negative amounts are almost always a model error
        if data[field] is not None and data[field] < 0:
            warnings.append(
                f"Negative value for '{field}': {data[field]}. Setting to None."
            )
            data[field] = None

    # ── Date fields ───────────────────────────────────────────────────────────
    for field in ("invoice_date", "due_date"):
        value, warn = _parse_date(data[field], field)
        data[field] = value
        if warn:
            warnings.append(warn)

    # ── String fields ─────────────────────────────────────────────────────────
    for field in ("invoice_id", "vendor_name", "currency",
                  "payment_status", "purchase_order_number"):
        val = data.get(field)
        if val is not None:
            cleaned = str(val).strip()
            data[field] = cleaned if cleaned else None

    # ── Normalise payment_status to uppercase enum ────────────────────────────
    ps = data.get("payment_status")
    if ps:
        ps_upper = ps.upper()
        if ps_upper not in ("PAID", "UNPAID", "OVERDUE"):
            warnings.append(
                f"Unexpected payment_status value: '{ps}'. "
                f"Expected PAID, UNPAID, or OVERDUE. Keeping as-is."
            )
        data["payment_status"] = ps_upper

    # ── Normalise currency to uppercase ───────────────────────────────────────
    if data.get("currency"):
        data["currency"] = data["currency"].upper()

    # ── Line items ────────────────────────────────────────────────────────────
    data["line_items"], item_warnings = _normalise_line_items(
        data.get("line_items") or []
    )
    warnings.extend(item_warnings)

    return data, warnings


def _to_float(value: Any, field_name: str) -> tuple[float | None, str | None]:
    """
    Convert a value to float, handling common invoice formatting.

    Returns (float_value, warning_message_or_None).

    Handles:
      - Plain numbers: 1250.00 → 1250.0
      - String with currency symbols: "$1,250.00" → 1250.0
      - European notation: "1.250,00" → 1250.0
      - Already a float or int: returned directly
    """
    if value is None:
        return None, None
    if isinstance(value, bool):
        return None, f"Boolean value for numeric field '{field_name}'; setting to None."
    if isinstance(value, (int, float)):
        return float(value), None
    if not isinstance(value, str):
        return None, f"Unexpected type {type(value).__name__} for '{field_name}'; setting to None."

    s = value.strip()

    # Detect European notation: has a period for thousands and comma for decimal
    # e.g. "1.250,00" — the comma comes after the period
    if re.search(r"\d\.\d{3},\d{2}", s):
        s = s.replace(".", "").replace(",", ".")

    # Strip everything except digits, decimal point, and minus sign
    cleaned = re.sub(r"[^\d.\-]", "", s)

    if not cleaned or cleaned == "-":
        return None, f"Could not parse numeric value '{value}' for field '{field_name}'."

    try:
        return float(cleaned), None
    except ValueError:
        return None, f"Could not convert '{value}' to number for field '{field_name}'."


def _parse_date(value: Any, field_name: str) -> tuple[str | None, str | None]:
    """
    Parse a date value and return it as a YYYY-MM-DD string.

    Tries multiple common date formats. Athena's date column type
    requires YYYY-MM-DD, so this conversion matters for analytics queries.

    Returns (date_string_or_None, warning_or_None).
    """
    if value is None:
        return None, None

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()

    if not value:
        return None, None

    # Already in the right format — fast path
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value, None

    # Try each known format
    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
            converted = parsed.strftime("%Y-%m-%d")
            logger.debug(
                "Converted date '%s' using format '%s' → '%s'", value, fmt, converted
            )
            return converted, None
        except ValueError:
            continue

    # Could not parse — keep the raw value but warn
    warn = (
        f"Could not parse date '{value}' for field '{field_name}'. "
        f"Keeping raw value. Athena date queries may not work for this record."
    )
    return value, warn


def _normalise_line_items(
    items: list,
) -> tuple[list[dict], list[str]]:
    """
    Normalise the line_items array.

    Each item is coerced to have: description (str), quantity (float),
    unit_price (float), line_total (float).

    Missing numeric fields are derived where possible:
      - If unit_price is missing: unit_price = line_total / quantity
      - If line_total is missing: line_total = quantity * unit_price
      - If quantity is missing: quantity = 1.0

    Returns (cleaned_items, warnings).
    """
    if not isinstance(items, list):
        return [], [f"line_items was not a list (got {type(items).__name__}); reset to []."]

    cleaned = []
    warnings = []

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            warnings.append(f"Line item #{i} is not an object; skipped.")
            continue

        desc = str(item.get("description") or "").strip()

        qty_val, qty_warn = _to_float(item.get("quantity"), f"line_items[{i}].quantity")
        if qty_warn:
            warnings.append(qty_warn)
        qty = qty_val if qty_val is not None else 1.0

        up_val, up_warn = _to_float(item.get("unit_price"), f"line_items[{i}].unit_price")
        if up_warn:
            warnings.append(up_warn)

        lt_val, lt_warn = _to_float(item.get("line_total"), f"line_items[{i}].line_total")
        if lt_warn:
            warnings.append(lt_warn)

        # Derive missing fields
        if up_val is None and lt_val is not None and qty > 0:
            up_val = round(lt_val / qty, 6)
        if lt_val is None and up_val is not None:
            lt_val = round(qty * up_val, 2)

        cleaned.append({
            "description": desc,
            "quantity":    qty,
            "unit_price":  up_val,
            "line_total":  lt_val,
        })

    return cleaned, warnings


def _check_amount_consistency(data: dict, warnings: list[str]) -> list[str]:
    """
    Check that subtotal + tax_amount ≈ total_amount.
    Log a warning if the difference exceeds _AMOUNT_TOLERANCE.

    This catches cases where Bedrock read numbers correctly but from
    the wrong rows (e.g. picked a subtotal from a different section).
    """
    subtotal = data.get("subtotal")
    tax      = data.get("tax_amount")
    total    = data.get("total_amount")

    if subtotal is not None and tax is not None and total is not None:
        computed = round(subtotal + tax, 2)
        diff = abs(computed - total)
        if diff > _AMOUNT_TOLERANCE:
            warnings.append(
                f"Amount inconsistency: subtotal ({subtotal}) + tax ({tax}) = "
                f"{computed}, but total_amount = {total}. "
                f"Difference: {diff:.2f}. Keeping total_amount as authoritative."
            )

    # If subtotal is missing but total and tax are present, derive subtotal
    if data.get("subtotal") is None and total is not None and tax is not None:
        data["subtotal"] = round(total - tax, 2)
        logger.debug("Derived subtotal = total - tax = %s", data["subtotal"])

    # If tax is missing but subtotal and total are present, derive tax
    if data.get("tax_amount") is None and total is not None and subtotal is not None:
        derived_tax = round(total - subtotal, 2)
        if derived_tax >= 0:
            data["tax_amount"] = derived_tax
            logger.debug("Derived tax_amount = total - subtotal = %s", derived_tax)

    return warnings
