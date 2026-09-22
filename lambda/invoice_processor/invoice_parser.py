"""
Invoice Parser — Energy Invoice Schema
---------------------------------------
WHAT IT IS:
  Parses and validates the raw Bedrock response for energy/colocation invoices.
  Normalises all field types, computes USD conversion, and attaches a
  data_quality_warnings list to every output record.

NEW SCHEMA (v3):
  vendor              — issuing company name
  invoice_number      — vendor's invoice reference
  invoice_date        — YYYY-MM-DD
  period              — YYYY-MM billing period
  currency            — 3-letter ISO code
  total_amount        — total due in local currency
  tax_amount          — tax portion in local currency
  total_volume_kwh    — electricity consumption in kWh
  base_rate           — energy rate per kWh in local currency
  current_pue         — actual PUE for the billing period
  pue_cap             — contractual PUE cap
  usd_rate            — exchange rate used (local currency units per 1 USD)
  total_amount_usd    — total_amount converted to USD

USD CONVERSION:
  usd_exchange_rates table is read from AppConfig config dict.
  Format: {"EUR": 0.92, "GBP": 0.79, ...}
  Meaning: 1 USD = X units of that currency.
  Conversion: total_amount_usd = total_amount / usd_rate

LAYER: Application code (runs inside AWS Lambda at runtime)
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

# Required fields — missing any of these raises ValueError (invoice not saved).
_REQUIRED_FIELDS = {"vendor", "invoice_number", "invoice_date", "total_amount"}

# All expected output fields with defaults.
_FIELD_DEFAULTS: dict[str, Any] = {
    "vendor":            None,
    "invoice_number":    None,
    "invoice_date":      None,
    "period":            None,
    "currency":          None,
    "total_amount":      None,
    "tax_amount":        None,
    "total_volume_kwh":  None,
    "base_rate":         None,
    "current_pue":       None,
    "pue_cap":           None,
    "usd_rate":          None,
    "total_amount_usd":  None,
}

# Date formats tried in order for invoice_date parsing.
_DATE_FORMATS = [
    "%Y-%m-%d",    # 2024-11-25  (preferred — Athena native)
    "%d/%m/%Y",    # 25/11/2024
    "%m/%d/%Y",    # 11/25/2024
    "%d-%m-%Y",    # 25-11-2024
    "%d.%m.%Y",    # 25.11.2024  (European)
    "%B %d, %Y",   # November 25, 2024
    "%d %B %Y",    # 25 November 2024
    "%b %d, %Y",   # Nov 25, 2024
    "%d %b %Y",    # 25 Nov 2024
    "%Y/%m/%d",    # 2024/11/25
    "%d/%m/%y",    # 25/11/24
    "%m/%d/%y",    # 11/25/24
]

# Period formats tried for YYYY-MM parsing.
_PERIOD_FORMATS = [
    "%Y-%m",       # 2024-09
    "%B %Y",       # September 2024
    "%b %Y",       # Sep 2024
    "%m/%Y",       # 09/2024
    "%m-%Y",       # 09-2024
]

# Amount consistency tolerance.
_AMOUNT_TOLERANCE = 0.50  # 50 cents — energy bills can have rounding


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def parse_and_validate(raw_text: str, config: dict | None = None) -> dict:
    """
    Parse the raw Bedrock response into a validated energy invoice dict.

    Parameters
    ----------
    raw_text : str
        Raw text from Bedrock — may contain markdown fences.
    config : dict, optional
        AppConfig configuration dict. Used to look up usd_exchange_rates.
        If None, USD conversion is skipped (usd_rate and total_amount_usd = None).

    Returns
    -------
    dict
        Clean invoice dict with all fields present plus data_quality_warnings.

    Raises
    ------
    ValueError
        If JSON cannot be extracted or required fields are missing.
    """
    warnings: list[str] = []

    # Step 1: extract JSON from raw text
    json_str = _extract_json_string(raw_text)

    # Step 2: parse
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Bedrock response is not valid JSON: {exc}\n"
            f"Raw text (first 400 chars): {raw_text[:400]}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object, got: {type(data).__name__}")

    # Step 3: fill defaults
    normalised = {**_FIELD_DEFAULTS, **data}

    # Step 4: normalise types
    normalised, warnings = _normalise_all_fields(normalised, warnings)

    # Step 5: validate required fields
    _validate_required_fields(normalised)

    # Step 6: USD conversion
    normalised, warnings = _apply_usd_conversion(normalised, config or {}, warnings)

    # Step 7: cross-field consistency
    warnings = _check_consistency(normalised, warnings)

    # Step 8: attach warnings
    normalised["data_quality_warnings"] = warnings

    if warnings:
        logger.warning(
            "Invoice %s parsed with %d warning(s): %s",
            normalised.get("invoice_number"), len(warnings), warnings,
        )
    else:
        logger.info(
            "Invoice parsed cleanly: invoice_number=%s vendor=%s "
            "total=%s %s usd=%s period=%s",
            normalised.get("invoice_number"),
            normalised.get("vendor"),
            normalised.get("total_amount"),
            normalised.get("currency", ""),
            normalised.get("total_amount_usd"),
            normalised.get("period"),
        )

    return normalised


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_json_string(text: str) -> str:
    """Extract JSON from text that may contain markdown fences or noise."""
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        logger.debug("Extracted JSON from markdown code fence")
        return fence.group(1).strip()

    brace = re.search(r"\{[\s\S]*\}", text)
    if brace:
        logger.debug("Extracted JSON via outermost brace matching")
        return brace.group(0).strip()

    logger.warning("Could not isolate JSON; attempting to parse full text")
    return text.strip()


def _validate_required_fields(data: dict) -> None:
    """Raise ValueError listing every required field that is null."""
    missing = [f for f in _REQUIRED_FIELDS if data.get(f) is None]
    if missing:
        raise ValueError(
            f"Invoice missing required fields: {missing}. "
            f"Available: { {k: v for k, v in data.items() if k not in ('data_quality_warnings',)} }"
        )


def _normalise_all_fields(data: dict, warnings: list[str]) -> tuple[dict, list[str]]:
    """Normalise types for all fields in the energy invoice schema."""

    # Numeric: monetary amounts
    for field in ("total_amount", "tax_amount"):
        val, warn = _to_float(data.get(field), field)
        data[field] = val
        if warn:
            warnings.append(warn)
        if data[field] is not None and data[field] < 0:
            warnings.append(f"Negative value for '{field}': {data[field]}. Setting to None.")
            data[field] = None

    # Numeric: energy-specific fields
    for field in ("total_volume_kwh", "base_rate", "current_pue", "pue_cap"):
        val, warn = _to_float(data.get(field), field)
        data[field] = val
        if warn:
            warnings.append(warn)
        if data[field] is not None and data[field] < 0:
            warnings.append(f"Negative value for '{field}': {data[field]}. Setting to None.")
            data[field] = None

    # PUE sanity check: PUE should be >= 1.0
    for pue_field in ("current_pue", "pue_cap"):
        val = data.get(pue_field)
        if val is not None and val < 1.0:
            warnings.append(
                f"'{pue_field}' value {val} is below 1.0 which is physically impossible. "
                f"Setting to None."
            )
            data[pue_field] = None

    # Date: invoice_date → YYYY-MM-DD
    val, warn = _parse_date(data.get("invoice_date"), "invoice_date")
    data["invoice_date"] = val
    if warn:
        warnings.append(warn)

    # Period: → YYYY-MM
    val, warn = _parse_period(data.get("period"), "period")
    data["period"] = val
    if warn:
        warnings.append(warn)

    # String fields
    for field in ("vendor", "invoice_number", "currency"):
        raw = data.get(field)
        if raw is not None:
            cleaned = str(raw).strip()
            data[field] = cleaned if cleaned else None

    # Currency → uppercase
    if data.get("currency"):
        data["currency"] = data["currency"].upper()

    return data, warnings


def _apply_usd_conversion(
    data: dict,
    config: dict,
    warnings: list[str],
) -> tuple[dict, list[str]]:
    """
    Compute usd_rate and total_amount_usd from the AppConfig exchange rate table.

    Logic:
      rates table format: {"EUR": 0.92, ...}  — meaning 1 USD = 0.92 EUR
      total_amount_usd = total_amount / rate

    If currency is USD, rate = 1.0 and total_amount_usd = total_amount.
    If currency not in table, logs a warning and skips conversion.
    """
    currency = data.get("currency")
    total    = data.get("total_amount")

    if not currency or total is None:
        warnings.append(
            "USD conversion skipped: currency or total_amount is missing."
        )
        return data, warnings

    rates: dict = config.get("usd_exchange_rates", {})

    if not rates:
        warnings.append(
            "USD conversion skipped: usd_exchange_rates not found in AppConfig."
        )
        return data, warnings

    if currency not in rates:
        warnings.append(
            f"USD conversion skipped: currency '{currency}' not in "
            f"usd_exchange_rates table. Available: {list(rates.keys())}"
        )
        return data, warnings

    rate = float(rates[currency])
    if rate <= 0:
        warnings.append(f"Invalid exchange rate for '{currency}': {rate}. Skipping conversion.")
        return data, warnings

    data["usd_rate"]         = rate
    data["total_amount_usd"] = round(total / rate, 2)

    logger.info(
        "USD conversion: %s %.4f × (1/%.4f) = USD %.2f",
        currency, total, rate, data["total_amount_usd"],
    )

    return data, warnings


def _check_consistency(data: dict, warnings: list[str]) -> list[str]:
    """
    Cross-field consistency checks for energy invoices.

    1. total_amount >= tax_amount
    2. base_rate × total_volume_kwh × current_pue ≈ net energy charge
    3. period month should match invoice_date month
    """
    total = data.get("total_amount")
    tax   = data.get("tax_amount")

    # Check 1: total >= tax
    if total is not None and tax is not None and tax > total:
        warnings.append(
            f"tax_amount ({tax}) exceeds total_amount ({total}). "
            f"Possible extraction error."
        )

    # Check 2: energy arithmetic
    volume   = data.get("total_volume_kwh")
    rate     = data.get("base_rate")
    pue      = data.get("current_pue")

    if volume is not None and rate is not None and pue is not None and tax is not None:
        net_amount = total - tax if total is not None else None
        if net_amount is not None:
            computed_energy_charge = round(volume * rate * pue, 2)
            diff = abs(computed_energy_charge - net_amount)
            # Allow 5% tolerance for additional fees (colocation, handling, etc.)
            tolerance = max(_AMOUNT_TOLERANCE, net_amount * 0.05)
            if diff > tolerance:
                warnings.append(
                    f"Energy arithmetic check: volume ({volume} kWh) × "
                    f"base_rate ({rate}) × PUE ({pue}) = {computed_energy_charge}, "
                    f"but net amount (total - tax) = {net_amount}. "
                    f"Difference: {diff:.2f}. May include additional fees."
                )

    # Check 3: period vs invoice_date
    invoice_date = data.get("invoice_date")
    period       = data.get("period")

    if invoice_date and period:
        try:
            inv_month = invoice_date[:7]  # "2024-11"
            if not period.startswith(inv_month[:4]):  # at least same year
                warnings.append(
                    f"period '{period}' year does not match "
                    f"invoice_date '{invoice_date}' year. Verify extraction."
                )
        except Exception:
            pass  # non-critical check

    return warnings


def _to_float(value: Any, field_name: str) -> tuple[float | None, str | None]:
    """Convert a value to float, handling currency formatting."""
    if value is None:
        return None, None
    if isinstance(value, bool):
        return None, f"Boolean for numeric field '{field_name}'; setting to None."
    if isinstance(value, (int, float)):
        return float(value), None
    if not isinstance(value, str):
        return None, f"Unexpected type {type(value).__name__} for '{field_name}'."

    s = value.strip()

    # European notation: "1.250,00" → "1250.00"
    if re.search(r"\d\.\d{3},\d{2}", s):
        s = s.replace(".", "").replace(",", ".")

    cleaned = re.sub(r"[^\d.\-]", "", s)

    if not cleaned or cleaned == "-":
        return None, f"Could not parse numeric value '{value}' for '{field_name}'."

    try:
        return float(cleaned), None
    except ValueError:
        return None, f"Could not convert '{value}' to number for '{field_name}'."


def _parse_date(value: Any, field_name: str) -> tuple[str | None, str | None]:
    """Parse a date and return YYYY-MM-DD, or the raw value with a warning."""
    if value is None:
        return None, None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if not value:
        return None, None

    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value, None

    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime("%Y-%m-%d"), None
        except ValueError:
            continue

    return value, (
        f"Could not parse date '{value}' for '{field_name}'. "
        f"Keeping raw value. Athena date queries may not work."
    )


def _parse_period(value: Any, field_name: str) -> tuple[str | None, str | None]:
    """
    Parse a billing period and return YYYY-MM format.

    Handles:
      "2024-09"           → "2024-09"  (already correct)
      "September 2024"    → "2024-09"
      "Sep 2024"          → "2024-09"
      "09/2024"           → "2024-09"
      "2024-09-01"        → "2024-09"  (truncate day)
    """
    if value is None:
        return None, None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if not value:
        return None, None

    # Already YYYY-MM
    if re.match(r"^\d{4}-\d{2}$", value):
        return value, None

    # YYYY-MM-DD — truncate to YYYY-MM
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value[:7], None

    # Try period formats
    for fmt in _PERIOD_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime("%Y-%m"), None
        except ValueError:
            continue

    return value, (
        f"Could not parse period '{value}' for '{field_name}'. "
        f"Expected YYYY-MM format. Keeping raw value."
    )
