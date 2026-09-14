"""
text_parser.py — Turns raw OCR text into a structured receipt record.

FIX APPLIED: this file previously contained an exact duplicate of
paddle_engine.py (a copy/paste mistake) instead of any parsing logic.
There was no code anywhere in the original repo that actually converted
OCR text -> {vendor, date, amount, tax, subtotal, bill_id}. That logic is
implemented here now.

Strategy:
  1. Try to match the text against a known vendor template (ocr/templates.py).
     If matched, use that template's field-specific regexes (more accurate).
  2. If no template matches, fall back to generic regex heuristics that work
     reasonably well across most receipt formats.
  3. Clean/normalize every extracted value with utils/helpers.py.
"""

import re
import uuid
from datetime import date as date_cls
from typing import Any, Dict, Optional

from ocr.templates import get_matching_template
from utils.helpers import normalize_text, clean_amount, clean_date


# ── Generic fallback patterns (used when no vendor template matches) ───────
_GENERIC_TOTAL_PATTERNS = [
    r"(?:grand\s+total|total\s+amount|net\s+amount|amount\s+due|total\s+due|total)\s*[:\-]?\s*[₹$Rs.]*\s*([\d,]+\.\d{1,2})",
    r"(?:grand\s+total|total\s+amount|total)\s*[:\-]?\s*[₹$Rs.]*\s*([\d,]+)",
]
_GENERIC_TAX_PATTERNS = [
    r"(?:tax|gst|vat|cgst|sgst|igst)\s*[:\-]?\s*[₹$Rs.]*\s*([\d,]+\.?\d{0,2})",
]
_GENERIC_SUBTOTAL_PATTERNS = [
    r"(?:sub\s*total|subtotal)\s*[:\-]?\s*[₹$Rs.]*\s*([\d,]+\.?\d{0,2})",
]
_GENERIC_DATE_PATTERNS = [
    r"(\d{4}-\d{2}-\d{2})",
    r"(\d{2}/\d{2}/\d{4})",
    r"(\d{2}-\d{2}-\d{4})",
    r"(\d{2}/\d{2}/\d{2})",
    r"(\d{1,2}\s+\w+\s+\d{4})",
]
_GENERIC_VENDOR_STOPWORDS = {"receipt", "invoice", "bill", "total", "tax", "date", "cash", "card"}


def _first_match(patterns, text: str) -> Optional[str]:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _guess_vendor(raw_text: str) -> str:
    """
    Heuristic: the vendor name is usually one of the first non-empty,
    mostly-alphabetic lines at the top of the receipt.
    """
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    for line in lines[:5]:
        lower = line.lower()
        letters = sum(c.isalpha() for c in line)
        if letters >= 3 and not any(sw in lower for sw in _GENERIC_VENDOR_STOPWORDS):
            return line.title()[:80]
    return "Unknown Vendor"


def _guess_category(vendor: str) -> str:
    """Very lightweight category guess based on vendor keywords."""
    v = vendor.lower()
    mapping = {
        "Food & Dining": ["swiggy", "zomato", "cafe", "restaurant", "food", "pizza", "dominos"],
        "Travel": ["uber", "ola", "indigo", "airlines", "flight", "cab", "taxi"],
        "Groceries": ["dmart", "bigbasket", "reliance fresh", "grocery", "mart"],
        "Utilities": ["bescom", "electricity", "water board", "gas"],
        "Shopping": ["amazon", "flipkart", "walmart", "target", "costco"],
    }
    for category, keywords in mapping.items():
        if any(k in v for k in keywords):
            return category
    return "Uncategorized"


def parse_receipt_text(raw_text: str) -> Dict[str, Any]:
    """
    Parse raw OCR text into a structured receipt dict, ready to hand to
    database.queries.save_receipt().

    Returns keys: bill_id, vendor, date, amount, tax, subtotal, category, raw_text
    """
    text = normalize_text(raw_text) if raw_text else ""
    template = get_matching_template(text) if text else None

    # BUG FIX: every vendor template's "total" regex (and the generic
    # fallback) matches the bare word "total" with no word boundary, which
    # also matches inside "Subtotal:". On a receipt listing both Subtotal
    # and Grand Total, this previously extracted the *subtotal* value as
    # the amount. Fix: strip the "Subtotal: <amount>" segment out of the
    # text used specifically for TOTAL extraction (subtotal is still
    # extracted separately, from the untouched original text).
    text_for_total = re.sub(
        r"sub[\s\-]*total\s*[:\-]?\s*[₹$Rs.]*\s*[\d,]+\.?\d*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    if template:
        vendor = template.name
        amount_str = template.extract_field("total", text_for_total)
        tax_str = template.extract_field("tax", text)
        subtotal_str = template.extract_field("subtotal", text)
        date_str = template.extract_field("date", text)
        bill_id = template.extract_field("bill_id", text)
    else:
        vendor = _guess_vendor(raw_text or "")
        amount_str = _first_match(_GENERIC_TOTAL_PATTERNS, text_for_total)
        tax_str = _first_match(_GENERIC_TAX_PATTERNS, text)
        subtotal_str = _first_match(_GENERIC_SUBTOTAL_PATTERNS, text)
        date_str = _first_match(_GENERIC_DATE_PATTERNS, text)
        bill_id = None

    amount = clean_amount(amount_str) if amount_str else None
    tax = clean_amount(tax_str) if tax_str else 0.0
    subtotal = clean_amount(subtotal_str) if subtotal_str else 0.0

    parsed_date = clean_date(date_str) if date_str else None
    date_out = parsed_date.isoformat() if isinstance(parsed_date, date_cls) else (date_str or date_cls.today().isoformat())

    if not bill_id:
        # Deterministic-looking but unique fallback ID, flagged so
        # check_receipt_duplicate() knows not to trust it as a real bill number.
        bill_id = f"REC-{uuid.uuid4().hex[:10].upper()}"

    return {
        "bill_id": bill_id,
        "vendor": vendor or "Unknown Vendor",
        "date": date_out,
        "amount": amount if amount is not None else 0.0,
        "tax": tax or 0.0,
        "subtotal": subtotal or (amount if amount is not None else 0.0),
        "category": _guess_category(vendor or ""),
        "raw_text": raw_text,
    }
