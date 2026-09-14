"""
templates.py — Receipt template definitions with pre-compiled regex patterns.

Fixes applied:
  - All regex patterns pre-compiled at module load (performance).
  - Fuzzy matching generalized for all templates.
  - Added Indian vendor templates (Swiggy, Zomato, Ola, Uber, BESCOM, etc.).
  - Added compiled_pattern field to dataclass.
  - Added currency-aware total extraction.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Pattern, Dict


@dataclass
class ReceiptTemplate:
    """
    Defines a regex-based template for a specific vendor layout.

    Patterns should use capturing groups for the values to extract.
    Example total_pattern: r"total\s+\$?\s*(\d+\.\d{2})"
    """
    name: str
    vendor_pattern: str          # Regex to identify this vendor
    date_pattern: Optional[str] = None
    total_pattern: Optional[str] = None
    tax_pattern: Optional[str] = None
    subtotal_pattern: Optional[str] = None
    bill_id_pattern: Optional[str] = None
    line_item_pattern: Optional[str] = None
    currency_symbol: str = "$"    # Default currency symbol for this vendor
    fuzzy_keywords: List[str] = field(default_factory=list)

    # Internal: compiled regex (set by __post_init__)
    _compiled: Dict[str, Pattern] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        """Pre-compile all regex patterns for performance."""
        patterns = {
            "vendor": self.vendor_pattern,
            "date": self.date_pattern,
            "total": self.total_pattern,
            "tax": self.tax_pattern,
            "subtotal": self.subtotal_pattern,
            "bill_id": self.bill_id_pattern,
            "line_item": self.line_item_pattern,
        }
        for key, pat in patterns.items():
            if pat is not None:
                try:
                    self._compiled[key] = re.compile(pat, re.IGNORECASE)
                except re.error as e:
                    raise ValueError(f"Invalid regex in {self.name}.{key}: {e}") from e

    def match_vendor(self, text: str) -> bool:
        """Check if the text matches this vendor's pattern."""
        if "vendor" not in self._compiled:
            return False
        return bool(self._compiled["vendor"].search(text))

    def match_fuzzy(self, text_lower: str) -> bool:
        """Check if any fuzzy keyword appears in the text."""
        return any(kw in text_lower for kw in self.fuzzy_keywords)

    def extract_field(self, field_name: str, text: str) -> Optional[str]:
        """Extract a field using the pre-compiled regex."""
        if field_name not in self._compiled:
            return None
        m = self._compiled[field_name].search(text)
        return m.group(1) if m and m.lastindex and m.lastindex >= 1 else None


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

TEMPLATES: List[ReceiptTemplate] = [
    # ─── US Retail ─────────────────────────────────────────────────────────
    ReceiptTemplate(
        name="Walmart",
        vendor_pattern=r"walmart",
        date_pattern=r"(\d{2}/\d{2}/\d{2,4})",
        total_pattern=r"total\s+due\s+\$?\s*([\d,]+\.\d{2})",
        tax_pattern=r"tax\s+\d+\s*\$?\s*([\d,]+\.\d{2})",
        bill_id_pattern=r"tc#\s*(\d+)",
        currency_symbol="$",
        fuzzy_keywords=["walmart", "wal mart", "wlmart"],
    ),
    ReceiptTemplate(
        name="Target",
        vendor_pattern=r"target",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        total_pattern=r"total\s+\$?\s*([\d,]+\.\d{2})",
        bill_id_pattern=r"receipt#\s*([a-zA-Z0-9-]+)",
        currency_symbol="$",
        fuzzy_keywords=["target", "trgt"],
    ),
    ReceiptTemplate(
        name="Costco",
        vendor_pattern=r"costco",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        total_pattern=r"total\s+owned\s+\$?\s*([\d,]+\.\d{2})",
        currency_symbol="$",
        fuzzy_keywords=["costco", "cstco"],
    ),
    ReceiptTemplate(
        name="Amazon",
        vendor_pattern=r"amazon",
        date_pattern=r"shipped\s+on\s+(\w+\s+\d{1,2},\s+\d{4})",
        total_pattern=r"grand\s+total[:\s]*\$?\s*([\d,]+\.\d{2})",
        bill_id_pattern=r"order\s*#\s*([0-9-]{10,})",
        currency_symbol="$",
        fuzzy_keywords=["amazon", "amzn"],
    ),

    # ─── Indian Retail & Services ───────────────────────────────────────────
    ReceiptTemplate(
        name="Swiggy",
        vendor_pattern=r"swiggy",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        total_pattern=r"(?:grand\s+total|total\s+amount|total)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        tax_pattern=r"(?:tax|gst)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        bill_id_pattern=r"(?:order\s*id|order\s*#|invoice)\s*[:\-]?\s*([A-Z0-9-]+)",
        currency_symbol="₹",
        fuzzy_keywords=["swiggy", "swigy", "swgg"],
    ),
    ReceiptTemplate(
        name="Zomato",
        vendor_pattern=r"zomato",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        total_pattern=r"(?:grand\s+total|total\s+amount|total)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        tax_pattern=r"(?:tax|gst)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        bill_id_pattern=r"(?:order\s*id|order\s*#|invoice)\s*[:\-]?\s*([A-Z0-9-]+)",
        currency_symbol="₹",
        fuzzy_keywords=["zomato", "zmt", "zomto"],
    ),
    ReceiptTemplate(
        name="Uber",
        vendor_pattern=r"uber",
        date_pattern=r"(\w+\s+\d{1,2},\s+\d{4}|\d{2}/\d{2}/\d{4})",
        total_pattern=r"(?:total|amount)\s*[:\-]?\s*[₹Rs.$]*\s*([\d,]+\.?\d{0,2})",
        bill_id_pattern=r"(?:trip|ride)\s*id[:\-]?\s*([a-zA-Z0-9-]+)",
        currency_symbol="₹",
        fuzzy_keywords=["uber", "ubr", "uber india"],
    ),
    ReceiptTemplate(
        name="Ola",
        vendor_pattern=r"ola",
        date_pattern=r"(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})",
        total_pattern=r"(?:total\s+fare|total\s+amount|total)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        bill_id_pattern=r"(?:crn|booking)\s*[:\-]?\s*([A-Z0-9]+)",
        currency_symbol="₹",
        fuzzy_keywords=["ola", "ola cabs", "olacabs"],
    ),
    ReceiptTemplate(
        name="BESCOM",
        vendor_pattern=r"bescom|bangalore\s+electricity",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        total_pattern=r"(?:total\s+amount\s+due|bill\s+amount|amount\s+due)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        bill_id_pattern=r"(?:rr\s*no|consumer\s*no)[:\-]?\s*([0-9]+)",
        currency_symbol="₹",
        fuzzy_keywords=["bescom", "bangalore electricity", "electricity"],
    ),
    ReceiptTemplate(
        name="IndiGo",
        vendor_pattern=r"indigo",
        date_pattern=r"(\d{2}\s+\w+\s+\d{4}|\d{2}/\d{2}/\d{4})",
        total_pattern=r"(?:total\s+amount|grand\s+total|total)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        tax_pattern=r"(?:tax|gst|igst|cgst|sgst)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        bill_id_pattern=r"(?:pnr|booking\s*ref)[:\-]?\s*([A-Z0-9]{6})",
        currency_symbol="₹",
        fuzzy_keywords=["indigo", "indgo", "6e", "goindigo"],
    ),
    ReceiptTemplate(
        name="Cafe Turmeric",
        vendor_pattern=r"cafe\s+turmeric|turmeric\s+cafe",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        total_pattern=r"(?:total|grand\s+total)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        currency_symbol="₹",
        fuzzy_keywords=["turmeric", "turmeric cafe", "cafe turmeric"],
    ),
    ReceiptTemplate(
        name="DMart",
        vendor_pattern=r"d\s*mart|dmart",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        total_pattern=r"(?:total|grand\s+total|net\s+amount)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        tax_pattern=r"(?:gst|tax)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        bill_id_pattern=r"(?:bill\s*no|invoice)\s*[:\-]?\s*([A-Z0-9]+)",
        currency_symbol="₹",
        fuzzy_keywords=["dmart", "d mart"],
    ),
    ReceiptTemplate(
        name="BigBasket",
        vendor_pattern=r"big\s*basket|bigbasket",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        total_pattern=r"(?:total|grand\s+total)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        bill_id_pattern=r"(?:order\s*id|order\s*#)\s*[:\-]?\s*([A-Z0-9-]+)",
        currency_symbol="₹",
        fuzzy_keywords=["bigbasket", "big basket"],
    ),
    ReceiptTemplate(
        name="Reliance Fresh",
        vendor_pattern=r"reliance\s*(?:fresh|smart|digital)",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        total_pattern=r"(?:total|grand\s+total)\s*[:\-]?\s*[₹Rs.]*\s*([\d,]+\.?\d{0,2})",
        currency_symbol="₹",
        fuzzy_keywords=["reliance", "reliance fresh", "reliance smart"],
    ),

    # ─── Other International ──────────────────────────────────────────────
    ReceiptTemplate(
        name="Wirral School Shops",
        vendor_pattern=r"wirral\s+school\s+shops",
        date_pattern=r"(\d{4}-\d{2}-\d{2})",
        total_pattern=r"total\s+amount\s+[₹Rs.]*\s*([\d,]+\.\d{2})",
        tax_pattern=r"tax\s+[₹Rs.]*\s*([\d,]+\.\d{2})",
        currency_symbol="₹",
        fuzzy_keywords=["wirral", "school shop"],
    ),
    ReceiptTemplate(
        name="Melaka Layout",
        vendor_pattern=r"melaka|maas",
        total_pattern=r"grand\s+total\s*[:\-\s]*([\d,]+[.,]\d{2,3})",
        subtotal_pattern=r"subtotal\s*[:\-\s]*([\d,]+[.,]\d{2,3})",
        currency_symbol="$",
        fuzzy_keywords=["melaka", "maas", "mlaka", "melka", "meaka"],
    ),
]

# Build a lookup index for fast fuzzy matching
_TEMPLATE_INDEX: Dict[str, ReceiptTemplate] = {}
for t in TEMPLATES:
    _TEMPLATE_INDEX[t.name.lower()] = t


def get_matching_template(text: str) -> Optional[ReceiptTemplate]:
    """
    Find the best matching template for the given OCR text.

    Priority:
      1. Exact regex match on vendor_pattern.
      2. Fuzzy keyword match (for OCR errors like 'Melaka' → 'MAAS').
      3. None if no match.

    Args:
        text: Raw OCR text from the receipt.

    Returns:
        Matching ReceiptTemplate or None.
    """
    text_lower = text.lower()

    # Pass 1: Exact regex match
    for tmpl in TEMPLATES:
        if tmpl.match_vendor(text):
            return tmpl

    # Pass 2: Fuzzy keyword fallback
    for tmpl in TEMPLATES:
        if tmpl.match_fuzzy(text_lower):
            return tmpl

    return None


def get_template_by_name(name: str) -> Optional[ReceiptTemplate]:
    """Look up a template by its exact name (case-insensitive)."""
    return _TEMPLATE_INDEX.get(name.lower())
