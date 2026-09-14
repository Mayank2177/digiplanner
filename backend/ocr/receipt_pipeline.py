"""
receipt_pipeline.py — NEW MODULE.

This is the piece that was entirely missing from the original backend.
`main.py` had a `/api/v1/ocr/process` endpoint that did nothing but return
{"status": "WIP"}. Meanwhile a fully-built OCR engine (image_preprocessing,
paddle_engine, pdf_processor) existed but was never called from any
endpoint.

This module wires it all together:
  file bytes (image or PDF) -> preprocessing -> OCR text -> parsed fields

It also falls back to pytesseract if PaddleOCR isn't installed/working,
since PaddleOCR is a heavy dependency that can fail to install on some
machines.
"""

import io
import tempfile
from pathlib import Path
from typing import Any, Dict

from PIL import Image

from ocr.image_preprocessing import preprocess_image
from ocr.pdf_processor import pdf_to_images, is_pdf
from ocr.text_parser import parse_receipt_text
from utils.logger import log_error, log_info
from config.config import OCR_LANG, OCR_ENGINE


class OCRProcessingError(Exception):
    """Raised when a file cannot be OCR'd (bad file, no engine available, etc.)."""
    pass


def _run_ocr(pil_image: Image.Image) -> str:
    """
    Extract text from a single preprocessed image.
    Tries PaddleOCR first (better accuracy), falls back to pytesseract.
    """
    engine_preference = OCR_ENGINE.lower()

    if engine_preference in ("auto", "paddle"):
        try:
            from ocr.paddle_engine import extract_text_paddle, PaddleOCRError
            try:
                return extract_text_paddle(pil_image, lang=OCR_LANG)
            except PaddleOCRError as e:
                log_error(f"PaddleOCR failed, falling back to Tesseract: {e}")
        except ImportError:
            log_info("PaddleOCR not installed, falling back to Tesseract.")

    # Fallback: pytesseract
    try:
        import pytesseract
        return pytesseract.image_to_string(pil_image)
    except Exception as e:
        raise OCRProcessingError(
            f"No working OCR engine available (PaddleOCR and Tesseract both failed): {e}"
        )


def process_receipt_file(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Full pipeline: raw uploaded file bytes -> structured receipt dict.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename: Original filename (used to detect image vs PDF).

    Returns:
        Dict with keys: bill_id, vendor, date, amount, tax, subtotal,
        category, raw_text  (ready for database.queries.save_receipt()).

    Raises:
        OCRProcessingError: If the file can't be read or OCR'd.
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

    # Preprocess for better OCR accuracy
    try:
        processed_image = preprocess_image(image, mode="simple")
    except Exception as e:
        log_error(f"Preprocessing failed, using original image: {e}")
        processed_image = image

    raw_text = _run_ocr(processed_image)

    if not raw_text or not raw_text.strip():
        raise OCRProcessingError(
            "No text could be extracted from this file. Try a clearer photo or scan."
        )

    parsed = parse_receipt_text(raw_text)
    log_info(f"Parsed receipt: vendor={parsed['vendor']} amount={parsed['amount']}")
    return parsed
