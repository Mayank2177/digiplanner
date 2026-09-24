"""
receipt_pipeline.py — DONUT-based receipt processing pipeline.

Replaced the previous OCR (PaddleOCR/Tesseract) + regex-based NLP approach
with DONUT (Document Understanding Transformer), an end-to-end vision model
that directly extracts structured data from document images.

This module wires it all together:
  file bytes (image or PDF) -> DONUT model -> structured receipt data

NO MORE:
  - Traditional OCR engines (PaddleOCR, Tesseract)
  - Regex parsing and template matching
  - Text preprocessing heuristics

DONUT handles document understanding end-to-end using computer vision.
"""

import io
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict
from datetime import date as date_cls
import signal

from PIL import Image

from ocr.pdf_processor import pdf_to_images, is_pdf
from ocr.donut_engine import extract_receipt_fields, DONUTError
from ocr.image_optimizer import optimize_image_for_ocr, get_image_info
from utils.helpers import clean_amount, clean_date
from utils.logger import log_error, log_info, log_warning


class OCRProcessingError(Exception):
    """Raised when a file cannot be processed (bad file, model failure, etc.)."""
    pass


class TimeoutError(Exception):
    """Raised when processing exceeds timeout."""
    pass


def _guess_category(vendor: str) -> str:
    """Lightweight category guess based on vendor keywords."""
    v = vendor.lower() if vendor else ""
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


def process_receipt_file(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Full pipeline: raw uploaded file bytes -> structured receipt dict using DONUT.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename: Original filename (used to detect image vs PDF).

    Returns:
        Dict with keys: bill_id, vendor, date, amount, tax, subtotal,
        category (ready for database.queries.save_receipt()).

    Raises:
        OCRProcessingError: If the file can't be read or processed.
    """
    suffix = Path(filename).suffix.lower()

    try:
        if suffix == ".pdf" or is_pdf(filename):
            # PDFs are rasterized to images first (only the first page is
            # processed — receipts are virtually always single-page).
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            try:
                pages = pdf_to_images(tmp_path, dpi=300)
            finally:
                Path(tmp_path).unlink(missing_ok=True)

            if not pages:
                raise OCRProcessingError("Could not render any pages from the PDF.")
            image = pages[0]
        else:
            image = Image.open(io.BytesIO(file_bytes))

    except OCRProcessingError:
        raise
    except Exception as e:
        raise OCRProcessingError(f"Could not read uploaded file: {e}")

    # Optimize image for faster processing
    img_info = get_image_info(image)
    log_info(f"Original image: {img_info['width']}x{img_info['height']} ({img_info['megapixels']}MP)")
    
    if img_info['megapixels'] > 1.5:  # Images larger than 1.5MP get resized
        image = optimize_image_for_ocr(image, max_dimension=1280)
        optimized_info = get_image_info(image)
        log_info(f"Optimized to: {optimized_info['width']}x{optimized_info['height']} ({optimized_info['megapixels']}MP)")

    # Use DONUT to extract structured data directly from the image
    try:
        extracted = extract_receipt_fields(image)
    except DONUTError as e:
        raise OCRProcessingError(f"DONUT processing failed: {e}")
    except Exception as e:
        raise OCRProcessingError(f"Unexpected error during receipt processing: {e}")

    # Clean and normalize extracted fields
    vendor = extracted.get("vendor") or "Unknown Vendor"
    date_str = extracted.get("date")
    amount_str = extracted.get("total")
    tax_str = extracted.get("tax")
    subtotal_str = extracted.get("subtotal")
    bill_id = extracted.get("bill_id")

    # Parse and validate amounts
    amount = clean_amount(amount_str) if amount_str else None
    tax = clean_amount(tax_str) if tax_str else 0.0
    subtotal = clean_amount(subtotal_str) if subtotal_str else 0.0

    # Parse date
    parsed_date = clean_date(date_str) if date_str else None
    date_out = (
        parsed_date.isoformat()
        if isinstance(parsed_date, date_cls)
        else (date_str or date_cls.today().isoformat())
    )

    # Generate bill_id if not extracted
    if not bill_id or not bill_id.strip():
        bill_id = f"REC-{uuid.uuid4().hex[:10].upper()}"

    # Calculate subtotal from amount and tax if not provided
    if amount is not None and not subtotal:
        subtotal = max(0.0, amount - tax)

    result = {
        "bill_id": bill_id,
        "vendor": vendor,
        "date": date_out,
        "amount": amount if amount is not None else 0.0,
        "tax": tax,
        "subtotal": subtotal if subtotal else (amount if amount is not None else 0.0),
        "category": _guess_category(vendor),
        "currency": extracted.get("currency", "USD"),
        "raw_text": "",  # DONUT doesn't produce raw text like OCR
        "line_items": extracted.get("line_items", []),  # Include extracted line items
    }

    log_info(f"DONUT parsed receipt: vendor={result['vendor']} amount={result['amount']} currency={result['currency']} line_items={len(result['line_items'])}")
    return result
