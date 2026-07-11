import re
from dataclasses import dataclass
from typing import List, Optional, Pattern

@dataclass
class ReceiptTemplate:
    """
    Defines a regex-based template for a specific vendor layout.
    """
    name: str
    vendor_pattern: str  # Regex to identify this vendor (e.g. "Walmart")
    date_pattern: Optional[str] = None
    total_pattern: Optional[str] = None
    tax_pattern: Optional[str] = None
    subtotal_pattern: Optional[str] = None
    bill_id_pattern: Optional[str] = None
    line_item_pattern: Optional[str] = None

# Define common templates
TEMPLATES: List[ReceiptTemplate] = [
    ReceiptTemplate(
        name="Walmart",
        vendor_pattern=r"(?i)walmart",
        date_pattern=r"(\d{2}/\d{2}/\d{2,4})",  # MM/DD/YY
        total_pattern=r"(?i)\btotal\s+due\s+\$?\s*(\d+\.\d{2})",
        tax_pattern=r"(?i)tax\s+\d+\s*\$?\s*(\d+\.\d{2})",
        bill_id_pattern=r"(?i)tc#\s*(\d+)"
    ),
    ReceiptTemplate(
        name="Target",
        vendor_pattern=r"(?i)target",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        total_pattern=r"(?i)\btotal\s+\$?\s*(\d+\.\d{2})",
        bill_id_pattern=r"(?i)receipt#\s*([a-zA-Z0-9-]+)"
    ),
    ReceiptTemplate(
        name="Costco",
        vendor_pattern=r"(?i)costco",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        total_pattern=r"(?i)total\s+owned\s+\$?\s*(\d+\.\d{2})",
    ),
    ReceiptTemplate(
        name="Amazon",
        vendor_pattern=r"(?i)amazon",
        date_pattern=r"(?i)shipped on\s+(\w+\s+\d{1,2},\s+\d{4})",
        total_pattern=r"(?i)grand total:\s*\$?\s*(\d+\.\d{2})",
        bill_id_pattern=r"(?i)order #\s*([0-9-]{10,})",
    ),
    ReceiptTemplate(
        name="Wirral School Shops",
        vendor_pattern=r"(?i)wirral school shops",
        date_pattern=r"(\d{4}-\d{2}-\d{2})",
        total_pattern=r"(?i)total\s+amount\s+₹?\s*(\d+\.\d{2})",
        tax_pattern=r"(?i)tax\s+₹?\s*(\d+\.\d{2})"
    ),
    ReceiptTemplate(
        name="Melaka Layout",
        vendor_pattern=r"(?i)melaka|maas",
        total_pattern=r"(?i)grand\s+total\s*[:\-\s]*(\d+[.,]\d{2,3})",
        subtotal_pattern=r"(?i)subtotal\s*[:\-\s]*(\d+[.,]\d{2,3})",
    ),
    # Generic fallback templates if needed
]


def get_matching_template(text: str) -> Optional[ReceiptTemplate]:
    """Finds the first template that matches the vendor pattern in the text."""
    text_lower = text.lower()
    for tmpl in TEMPLATES:
        # Standard regex match
        if re.search(tmpl.vendor_pattern, text):
            return tmpl
        # Fuzzy fallback for known vendors (e.g. if 'Melaka' is read as 'MAAS')
        if tmpl.name == "Melaka Layout":
            if any(fuzzy in text_lower for fuzzy in ["maas", "mlaka", "melka", "meaka"]):
                return tmpl
    return None
