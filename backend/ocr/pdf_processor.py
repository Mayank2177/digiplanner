"""
pdf_processor.py — PDF to Image conversion and logging utilities.

Previously this file only contained logging. Now it handles:
  - PDF rasterization (pdf2image / PyMuPDF fallback)
  - Logging infrastructure
  - PDF text layer extraction (for hybrid OCR pipeline)
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from PIL import Image

# ─── Logging Setup ──────────────────────────────────────────────────────────
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("receipt_pipeline")


def log_info(message: str):
    """Log an informational message."""
    logger.info(message)


def log_error(message: str):
    """Log an error message."""
    logger.error(message)


# ─── PDF Processing ─────────────────────────────────────────────────────────

def pdf_to_images(
    pdf_path: str,
    dpi: int = 300,
    fmt: str = "RGB",
    first_page: Optional[int] = None,
    last_page: Optional[int] = None,
) -> List[Image.Image]:
    """
    Convert a PDF file to a list of PIL Images.

    Tries pdf2image first (best quality), falls back to PyMuPDF (fitz)
    if pdf2image is not installed.

    Args:
        pdf_path: Path to the PDF file.
        dpi: Resolution for rasterization (default 300).
        fmt: Color mode for output images ("RGB", "L", etc.).
        first_page: 1-based index of first page to convert (None = from start).
        last_page: 1-based index of last page to convert (None = to end).

    Returns:
        List of PIL Image objects, one per page.

    Raises:
        FileNotFoundError: If pdf_path does not exist.
        ImportError: If neither pdf2image nor PyMuPDF is installed.
        RuntimeError: If conversion fails.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Try pdf2image first (higher quality, uses poppler)
    try:
        from pdf2image import convert_from_path
        log_info(f"Converting PDF with pdf2image (dpi={dpi}): {pdf_path}")
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            fmt="png" if fmt == "RGB" else "jpeg",
            first_page=first_page,
            last_page=last_page,
        )
        # Ensure consistent mode
        return [img.convert(fmt) for img in images]
    except ImportError:
        pass

    # Fallback to PyMuPDF (fitz)
    try:
        import fitz  # PyMuPDF
        log_info(f"Converting PDF with PyMuPDF (dpi={dpi}): {pdf_path}")
        doc = fitz.open(pdf_path)
        images = []

        start = (first_page - 1) if first_page else 0
        end = (last_page - 1) if last_page else (len(doc) - 1)

        for page_num in range(start, end + 1):
            page = doc.load_page(page_num)
            # zoom matrix for target DPI (72 is MuPDF default)
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            if fmt != "RGB":
                img = img.convert(fmt)
            images.append(img)

        doc.close()
        return images
    except ImportError:
        raise ImportError(
            "PDF processing requires either 'pdf2image' (with poppler) "
            "or 'PyMuPDF' (fitz). Install one:
"
            "  pip install pdf2image  # also install poppler-utils
"
            "  pip install PyMuPDF"
        )
    except Exception as e:
        log_error(f"PDF conversion failed for {pdf_path}: {e}")
        raise RuntimeError(f"Failed to convert PDF: {e}") from e


def extract_pdf_text_layer(pdf_path: str) -> List[str]:
    """
    Extract embedded text from each page of a PDF (no OCR).

    Useful for hybrid pipelines: if the PDF already has a text layer,
    skip OCR entirely.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of strings, one per page.
    """
    try:
        import fitz
    except ImportError:
        log_error("PyMuPDF not installed; cannot extract text layer.")
        return []

    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        texts.append(page.get_text())
    doc.close()
    return texts


def is_pdf(path: str) -> bool:
    """Check if a file path points to a PDF."""
    return Path(path).suffix.lower() == ".pdf"
