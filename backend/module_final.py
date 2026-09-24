"""
UNIFIED RECEIPT EXTRACTION MODULE — PRODUCTION BUILD
=====================================================
Pipeline: File Upload → Validation → OCR Preprocessing → DONUT Extraction → SQL Storage

Usage:
    from receipt_extractor import process_and_store_receipt

    with open("receipt.jpg", "rb") as fh:
        result = process_and_store_receipt(fh.read(), "receipt.jpg", "user@example.com")

CLI:
    python receipt_extractor.py receipt.jpg --email user@example.com
    python receipt_extractor.py receipt.jpg --no-store
"""

from __future__ import annotations

import io
import logging
import os
import re
import sqlite3
import tempfile
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, date as date_cls
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, TypedDict, Union

import torch
from PIL import Image, UnidentifiedImageError

__version__ = "2.0.0"

__all__ = [
    "process_and_store_receipt",
    "process_receipt_file",
    "init_db",
    "get_settings",
    "Settings",
    "ReceiptDict",
    "LineItemDict",
    "ReceiptExtractionError",
    "FileValidationError",
    "OCRProcessingError",
    "DONUTError",
    "DatabaseError",
    "DuplicateReceiptError",
    # Database API
    "save_receipt",
    "check_receipt_duplicate",
    "receipt_exists",
    "fetch_all_receipts",
    "get_receipt_by_id",
    "update_receipt",
    "search_receipts",
    "delete_receipt",
    "clear_all_receipts",
    "get_user_by_email",
    "create_user",
    "update_user_budget",
]

# PIL decompression-bomb guard (raises beyond this pixel count).
Image.MAX_IMAGE_PIXELS = 100_000_000

# ============================================================================
# CONSTANTS
# ============================================================================

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
AUTOGEN_ID_PREFIX = "REC-"
DEFAULT_CURRENCY = "USD"
DEFAULT_CATEGORY = "Uncategorized"

# Extraction bounds (from proven DONUT heuristics).
MIN_TOTAL_AMOUNT = 0.01
MAX_TOTAL_AMOUNT = 10_000.0
MIN_LINE_ITEM_PRICE = 0.10
MAX_LINE_ITEM_PRICE = 500.0
MIN_VALID_SUBTOTAL = 0.50
SUBTOTAL_TOTAL_RATIO_LIMIT = 0.95
TOTAL_VALIDATION_TOLERANCE = 0.10

DATE_INPUT_FORMATS = (
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%d %b %Y",
    "%d %B %Y",
)

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Food & Dining": ["swiggy", "zomato", "cafe", "restaurant", "food", "pizza", "dominos"],
    "Travel": ["uber", "ola", "indigo", "airlines", "flight", "cab", "taxi"],
    "Groceries": ["dmart", "bigbasket", "reliance fresh", "grocery", "mart"],
    "Utilities": ["bescom", "electricity", "water board", "gas"],
    "Shopping": ["amazon", "flipkart", "walmart", "target", "costco"],
}

CURRENCY_MAP = {
    "$": "USD", "₹": "INR", "€": "EUR", "£": "GBP", "¥": "JPY",
    "USD": "USD", "INR": "INR", "EUR": "EUR", "GBP": "GBP", "JPY": "JPY",
}

# Pre-compiled patterns (hot path).
_CURRENCY_SYMBOLS_RE = re.compile(r"[\$€£¥₹]")
_LETTERS_RE = re.compile(r"[a-zA-Z]")
_NON_NUMERIC_RE = re.compile(r"[^\d.]")
_AMOUNT_RE = re.compile(r"(\d+[.,]?\d*)")
_PRICE_LIKE_ID_RE = re.compile(r"^\$?\d+\.\d{2}$")

_DATE_VALIDATION_PATTERNS = (
    re.compile(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"),
    re.compile(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}"),
    re.compile(r"\d{1,2}\s+\w+\s+\d{4}"),
    re.compile(r"\w{3}\s+\d{1,2},?\s+\d{4}"),
)

_LINE_ITEM_SKIP_KEYWORDS = (
    "restaurant", "cafe", "ca ", "phone", "date:", "table:", "server:", "bill:", "receipt",
)

_BUSINESS_NAME_HINTS = (
    "restaurant", "cafe", "shop", "store", "bar", "grill", "kitchen", "diner", "bistro",
)


# ============================================================================
# CONFIGURATION
# ============================================================================

def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except (TypeError, ValueError):
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, str(default)))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable runtime configuration. Load via Settings.from_env()."""

    base_dir: Path
    data_dir: Path
    db_path: Path
    log_dir: Path
    log_file: Path
    log_level: str
    log_max_bytes: int
    log_backup_count: int
    model_dir: Path
    model_name: str
    hf_cache_dir: Path
    max_file_size_bytes: int
    max_image_dimension: int
    image_optimize_threshold_mp: float
    pdf_dpi: int
    device: str

    @classmethod
    def from_env(cls, base_dir: Optional[Path] = None) -> "Settings":
        base = (base_dir or Path(__file__).resolve().parent).resolve()
        data_dir = Path(_env("RECEIPT_DATA_DIR", str(base / "data")))
        log_dir = Path(_env("RECEIPT_LOG_DIR", str(base / "logs")))
        return cls(
            base_dir=base,
            data_dir=data_dir,
            db_path=Path(_env("RECEIPT_DB_PATH", str(data_dir / "receipts.db"))),
            log_dir=log_dir,
            log_file=log_dir / "app.log",
            log_level=_env("RECEIPT_LOG_LEVEL", "INFO").upper(),
            log_max_bytes=_env_int("RECEIPT_LOG_MAX_BYTES", 10 * 1024 * 1024),
            log_backup_count=_env_int("RECEIPT_LOG_BACKUP_COUNT", 5),
            model_dir=Path(_env("RECEIPT_MODEL_DIR", str(base / "models" / "donut_model"))),
            model_name=_env("RECEIPT_MODEL_NAME", "naver-clova-ix/donut-base-finetuned-cord-v2"),
            hf_cache_dir=Path(_env("HF_HOME", str(base / "models" / "hf_cache"))),
            max_file_size_bytes=_env_int("RECEIPT_MAX_FILE_SIZE_MB", 20) * 1024 * 1024,
            max_image_dimension=_env_int("RECEIPT_MAX_IMAGE_DIM", 1280),
            image_optimize_threshold_mp=_env_float("RECEIPT_OPTIMIZE_THRESHOLD_MP", 1.5),
            pdf_dpi=_env_int("RECEIPT_PDF_DPI", 300),
            device=_env("RECEIPT_DEVICE", "cuda" if torch.cuda.is_available() else "cpu"),
        )

    def ensure_directories(self) -> None:
        for directory in (self.data_dir, self.log_dir, self.model_dir, self.hf_cache_dir):
            directory.mkdir(parents=True, exist_ok=True)


_settings: Optional[Settings] = None
_settings_lock = threading.Lock()


def get_settings() -> Settings:
    """Thread-safe settings singleton. Sets HF_HOME before transformers loads."""
    global _settings
    if _settings is None:
        with _settings_lock:
            if _settings is None:
                settings = Settings.from_env()
                settings.ensure_directories()
                os.environ.setdefault("HF_HOME", str(settings.hf_cache_dir))
                _settings = settings
    return _settings


# ============================================================================
# LOGGING
# ============================================================================

def configure_logging(settings: Settings) -> logging.Logger:
    """Idempotent logger setup: rotating file + console handlers."""
    log = logging.getLogger("receipt_extractor")
    if log.handlers:
        return log

    log.setLevel(getattr(logging, settings.log_level, logging.INFO))
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
    )

    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    log.addHandler(file_handler)
    log.addHandler(console_handler)
    log.propagate = False
    return log


logger = configure_logging(get_settings())


# ============================================================================
# EXCEPTIONS
# ============================================================================

class ReceiptExtractionError(Exception):
    """Base exception for all receipt extraction failures."""


class FileValidationError(ReceiptExtractionError):
    """Uploaded file failed validation (size, type, or content)."""


class OCRProcessingError(ReceiptExtractionError):
    """File could not be rendered or converted for OCR."""


class DONUTError(ReceiptExtractionError):
    """DONUT model loading or inference failed."""


class DatabaseError(ReceiptExtractionError):
    """Database operation failed (transaction rolled back)."""


class DuplicateReceiptError(ReceiptExtractionError):
    """Receipt already exists for this user."""


# ============================================================================
# DOMAIN TYPES
# ============================================================================

class LineItemDict(TypedDict):
    name: str
    quantity: int
    unit_price: float
    total_price: float


class ReceiptDict(TypedDict):
    bill_id: str
    vendor: str
    date: str
    amount: float
    tax: float
    subtotal: float
    category: str
    currency: str
    raw_text: str
    line_items: List[LineItemDict]


class FileType(str, Enum):
    PDF = "pdf"
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    TIFF = "tiff"
    BMP = "bmp"


# ============================================================================
# FILE VALIDATION
# ============================================================================

def detect_file_type(data: bytes) -> Optional[FileType]:
    """Sniff file type from magic bytes (never trust the extension)."""
    if data.startswith(b"%PDF-"):
        return FileType.PDF
    if data.startswith(b"\xff\xd8\xff"):
        return FileType.JPEG
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return FileType.PNG
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return FileType.WEBP
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return FileType.TIFF
    if data.startswith(b"BM"):
        return FileType.BMP
    return None


def validate_upload(file_bytes: bytes, filename: str, settings: Settings) -> FileType:
    """Validate size, extension, and content. Returns detected FileType."""
    if not file_bytes:
        raise FileValidationError("Empty file uploaded.")

    if len(file_bytes) > settings.max_file_size_bytes:
        limit_mb = settings.max_file_size_bytes // (1024 * 1024)
        raise FileValidationError(
            f"File size {len(file_bytes) / (1024 * 1024):.1f}MB exceeds {limit_mb}MB limit."
        )

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported extension '{extension}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )

    file_type = detect_file_type(file_bytes)
    if file_type is None:
        raise FileValidationError(
            f"File content does not match any supported format (filename: {filename})."
        )

    return file_type


# ============================================================================
# HELPER UTILITIES
# ============================================================================

def clean_amount(text: Optional[str]) -> Optional[float]:
    """Extract the first valid numeric amount from text."""
    if not text:
        return None
    match = _AMOUNT_RE.search(str(text))
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None
    return None


def clean_date(text: Optional[str]) -> Optional[date_cls]:
    """Try to parse a date from OCR text against known formats."""
    if not text:
        return None
    stripped = str(text).strip()
    for fmt in DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(stripped, fmt).date()
        except ValueError:
            continue
    return None


def guess_category(vendor: Optional[str]) -> str:
    """Lightweight category guess based on vendor keywords."""
    vendor_lower = (vendor or "").lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in vendor_lower for keyword in keywords):
            return category
    return DEFAULT_CATEGORY


# ============================================================================
# PDF PROCESSING
# ============================================================================

def pdf_to_images(
    pdf_path: Union[str, Path],
    dpi: int = 300,
    fmt: str = "RGB",
    first_page: Optional[int] = None,
    last_page: Optional[int] = None,
) -> List[Image.Image]:
    """Convert a PDF to PIL Images. Prefers pdf2image, falls back to PyMuPDF."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        from pdf2image import convert_from_path  # type: ignore

        logger.info("Converting PDF with pdf2image (dpi=%d): %s", dpi, path.name)
        images = convert_from_path(
            str(path),
            dpi=dpi,
            fmt="png" if fmt == "RGB" else "jpeg",
            first_page=first_page,
            last_page=last_page,
        )
        return [img.convert(fmt) for img in images]
    except ImportError:
        logger.debug("pdf2image unavailable, falling back to PyMuPDF.")

    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "PDF processing requires 'pdf2image' or 'PyMuPDF'. "
            "Install one: pip install pdf2image OR pip install PyMuPDF"
        ) from exc

    logger.info("Converting PDF with PyMuPDF (dpi=%d): %s", dpi, path.name)
    doc = None
    try:
        doc = fitz.open(str(path))
        page_count = len(doc)
        start = max((first_page - 1) if first_page else 0, 0)
        end = min((last_page - 1) if last_page else page_count - 1, page_count - 1)

        images: List[Image.Image] = []
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        for page_num in range(start, end + 1):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            images.append(img.convert(fmt) if fmt != "RGB" else img)
        return images
    except Exception as exc:
        logger.error("PDF conversion failed for %s: %s", path.name, exc)
        raise OCRProcessingError(f"Failed to convert PDF: {exc}") from exc
    finally:
        if doc is not None:
            doc.close()


# ============================================================================
# IMAGE OPTIMIZATION
# ============================================================================

def get_image_info(image: Image.Image) -> Dict[str, Any]:
    """Image metadata for logging."""
    return {
        "size": image.size,
        "mode": image.mode,
        "width": image.width,
        "height": image.height,
        "megapixels": round((image.width * image.height) / 1_000_000, 2),
    }


def optimize_image_for_ocr(image: Image.Image, max_dimension: int = 1280) -> Image.Image:
    """Normalize to RGB and downscale longest side to max_dimension (LANCZOS)."""
    if image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    if width <= max_dimension and height <= max_dimension:
        return image

    if width > height:
        new_size = (max_dimension, int((max_dimension / width) * height))
    else:
        new_size = (int((max_dimension / height) * width), max_dimension)

    return image.resize(new_size, Image.Resampling.LANCZOS)


# ============================================================================
# DONUT EXTRACTION ENGINE
# ============================================================================

def clean_price_string(value: Any) -> Optional[str]:
    """Strip currency symbols/formatting; reject non-numeric or out-of-range values."""
    if value is None:
        return None

    value_str = str(value).strip()

    # Reject values containing letters (other than currency symbols).
    if _LETTERS_RE.search(value_str):
        if _LETTERS_RE.search(_CURRENCY_SYMBOLS_RE.sub("", value_str)):
            return None

    value_str = _CURRENCY_SYMBOLS_RE.sub("", value_str)
    value_str = value_str.replace(",", "").replace("(", "").replace(")", "")
    value_str = _NON_NUMERIC_RE.sub("", value_str)

    try:
        float_val = float(value_str)
    except ValueError:
        return None

    if not (MIN_TOTAL_AMOUNT <= float_val <= MAX_TOTAL_AMOUNT):
        return None
    # Reject bare integers that look like quantities/IDs rather than prices.
    if float_val > 999 and "." not in str(value):
        return None
    return value_str


def validate_date(date_str: Any) -> bool:
    """Check whether a string matches any known date pattern."""
    if not date_str:
        return False
    text = str(date_str)
    return any(pattern.search(text) for pattern in _DATE_VALIDATION_PATTERNS)


class ReceiptProcessor:
    """DONUT CORD-v2 receipt processor with robust extraction heuristics."""

    def __init__(self, settings: Settings):
        self._settings = settings
        try:
            # Lazy import: keeps module import fast and lets HF_HOME be set first.
            from transformers import DonutProcessor, VisionEncoderDecoderModel

            model_dir = settings.model_dir
            model_dir.mkdir(parents=True, exist_ok=True)

            logger.info("Loading DONUT model: %s", settings.model_name)
            logger.info("Model directory: %s", model_dir)

            if (model_dir / "config.json").exists():
                logger.info("Loading DONUT from local cache.")
                self.processor = DonutProcessor.from_pretrained(str(model_dir))
                self.model = VisionEncoderDecoderModel.from_pretrained(str(model_dir))
            else:
                logger.info(
                    "First-time download of DONUT model (~800MB); saving to %s", model_dir
                )
                self.processor = DonutProcessor.from_pretrained(settings.model_name)
                self.model = VisionEncoderDecoderModel.from_pretrained(settings.model_name)
                self.processor.save_pretrained(str(model_dir))
                self.model.save_pretrained(str(model_dir))
                logger.info("Model saved locally; subsequent startups load from cache.")

            self.device = settings.device
            self.model.to(self.device)
            self.model.eval()  # Critical: disable dropout/training behavior at inference.

            logger.info("DONUT CORD-v2 loaded on device=%s", self.device)

        except ImportError as exc:
            logger.error("transformers/torch not installed: %s", exc)
            raise DONUTError(
                "transformers not installed. Run: pip install transformers torch"
            ) from exc
        except Exception as exc:
            logger.error("Failed to load DONUT model: %s", exc)
            raise DONUTError(f"Could not initialize DONUT: {exc}") from exc

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def extract_receipt_data(self, image: Image.Image) -> Dict[str, Any]:
        """Extract structured receipt data using DONUT CORD-v2."""
        try:
            if image.mode != "RGB":
                image = image.convert("RGB")

            pixel_values = self.processor(
                image, return_tensors="pt"
            ).pixel_values.to(self.device)

            task_prompt = "<s_cord-v2>"
            decoder_input_ids = self.processor.tokenizer(
                task_prompt, add_special_tokens=False, return_tensors="pt"
            ).input_ids.to(self.device)

            logger.info("Running DONUT CORD-v2 inference.")
            outputs = self.model.generate(
                pixel_values,
                decoder_input_ids=decoder_input_ids,
                max_length=self.model.config.decoder.max_position_embeddings,
                pad_token_id=self.processor.tokenizer.pad_token_id,
                eos_token_id=self.processor.tokenizer.eos_token_id,
                use_cache=True,
                bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                return_dict_in_generate=True,
                num_beams=1,
                early_stopping=True,
            )

            sequence = self.processor.batch_decode(outputs.sequences)[0]
            logger.debug("DONUT raw output (first 300 chars): %s", sequence[:300])

            sequence = (
                sequence.replace(self.processor.tokenizer.eos_token, "")
                .replace(self.processor.tokenizer.pad_token, "")
                .replace(task_prompt, "")
            )

            try:
                parsed_json = self.processor.token2json(sequence)
            except Exception as parse_error:
                logger.error("Failed to parse DONUT output to JSON: %s", parse_error)
                return self._get_empty_extraction()

            return self._normalize_cord_output(parsed_json)

        except DONUTError:
            raise
        except Exception as exc:
            logger.error("DONUT inference failed: %s", exc)
            raise DONUTError(f"Receipt extraction failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Normalization (proven heuristics — logic preserved verbatim)
    # ------------------------------------------------------------------

    def _normalize_cord_output(self, cord_json: Dict) -> Dict[str, Any]:
        """Normalize raw CORD-v2 JSON into a flat receipt structure."""
        try:
            vendor = self._extract_vendor(cord_json)

            financial = self._collect_financial_fields(cord_json, "root")

            total = str(max(financial["totals"])) if financial["totals"] else None
            tax = str(max(financial["taxes"])) if financial["taxes"] else None
            service_charge = (
                str(max(financial["service_charges"]))
                if financial["service_charges"]
                else None
            )
            subtotal = self._select_subtotal(financial["subtotals"], total, tax)

            # Validation + auto-correction.
            if total and tax:
                try:
                    total_num = float(total)
                    tax_num = float(tax)
                    service_num = float(service_charge) if service_charge else 0.0

                    if subtotal:
                        subtotal_num = float(subtotal)
                        calculated_total = subtotal_num + tax_num + service_num
                        diff = abs(calculated_total - total_num)

                        if diff / total_num <= TOTAL_VALIDATION_TOLERANCE:
                            logger.info(
                                "Validation passed: %.2f + %.2f + %.2f ~= %.2f",
                                subtotal_num, tax_num, service_num, total_num,
                            )
                        else:
                            logger.warning(
                                "Total validation failed: subtotal(%s) + tax(%s) + "
                                "service(%.2f) = %.2f != total(%s)",
                                subtotal, tax, service_num, calculated_total, total,
                            )
                            corrected = total_num - tax_num - service_num
                            if corrected > 0:
                                logger.info(
                                    "Auto-correcting subtotal: %s -> %.2f", subtotal, corrected
                                )
                                subtotal = str(corrected)
                    else:
                        calculated_subtotal = total_num - tax_num - service_num
                        if calculated_subtotal > 0:
                            subtotal = str(calculated_subtotal)
                            logger.info("Calculated subtotal: %s", subtotal)

                except (ValueError, ZeroDivisionError):
                    pass

            date = self._search_for_date(cord_json)
            bill_id = self._extract_bill_id(cord_json)

            result = {
                "vendor": vendor,
                "date": date,
                "total": total,
                "tax": tax,
                "subtotal": subtotal,
                "bill_id": bill_id,
                "currency": self._detect_currency(cord_json),
                "line_items": self._extract_line_items(cord_json),
            }

            if not vendor:
                logger.warning("Could not extract vendor name from receipt.")
            if not total:
                logger.warning("Could not extract total amount from receipt.")

            return result

        except Exception as exc:
            logger.error("Error normalizing CORD output: %s", exc)
            return self._get_empty_extraction()

    def _extract_vendor(self, cord_json: Dict) -> Optional[str]:
        """Vendor from store_info variants, with menu.nm fallback heuristics."""
        for store_key in ("store_info", "store", "company", "merchant"):
            store_obj = cord_json.get(store_key)
            if isinstance(store_obj, dict):
                vendor = (
                    store_obj.get("name")
                    or store_obj.get("store_name")
                    or store_obj.get("company")
                )
                if vendor:
                    return vendor

        menu = cord_json.get("menu")
        if isinstance(menu, dict):
            vendor = menu.get("nm")
            if vendor:
                logger.info("Extracted vendor from menu.nm: %s", vendor)
                return vendor
        elif isinstance(menu, list) and menu:
            first_item = menu[0]
            if isinstance(first_item, dict):
                first_nm = first_item.get("nm", "")
                has_valid_price = bool(clean_price_string(first_item.get("price")))
                looks_like_business = any(
                    word in first_nm.lower() for word in _BUSINESS_NAME_HINTS
                )
                if first_nm and (not has_valid_price or looks_like_business):
                    logger.info("Extracted vendor from menu[0].nm: %s", first_nm)
                    return first_nm
        return None

    def _collect_financial_fields(self, obj: Any, path: str) -> Dict[str, List[float]]:
        """Recursively gather totals/taxes/subtotals/service charges from CORD JSON."""
        found: Dict[str, List[float]] = {
            "totals": [],
            "taxes": [],
            "subtotals": [],
            "service_charges": [],
        }

        if isinstance(obj, dict):
            for key in ("total_price", "total", "grand_total", "final_total"):
                if key in obj:
                    value = obj[key]
                    if isinstance(value, str) and ("%" in value or "tip" in value.lower()):
                        continue
                    cleaned = clean_price_string(value)
                    if cleaned:
                        found["totals"].append(float(cleaned))
                        logger.debug("Found total at %s.%s: %s", path, key, cleaned)

            for key in ("cashprice", "changeprice"):
                if key in obj:
                    value = obj[key]
                    if isinstance(value, str) and (
                        "%" in value or "tip" in value.lower() or ":" in value
                    ):
                        logger.debug("Skipping %s at %s (tip suggestion): %s", key, path, value)
                        continue
                    cleaned = clean_price_string(value)
                    if cleaned:
                        found["totals"].append(float(cleaned))
                        logger.debug("Found total at %s.%s: %s", path, key, cleaned)

                        for key in ("tax_price", "tax", "TAX"):
                if key in obj:
                    value = obj[key]
                    if isinstance(value, str) and ("(" in value or ")" in value):
                        logger.debug("Skipping %s at %s (parentheses): %s", key, path, value)
                        continue
                    cleaned = clean_price_string(value)
                    if cleaned:
                        found["taxes"].append(float(cleaned))
                        logger.debug("Found tax at %s.%s: %s", path, key, cleaned)

            for key in ("subtotal_price", "subtotal", "Subtotal"):
                if key in obj:
                    cleaned = clean_price_string(obj[key])
                    if cleaned:
                        parent_is_service_charge = False
                        if "nm" in obj:
                            nm_lower = str(obj["nm"]).lower()
                            if "service" in nm_lower and "charge" in nm_lower:
                                parent_is_service_charge = True
                                found["totals"].append(float(cleaned))
                                logger.debug(
                                    "Found FINAL TOTAL at %s.%s (service charge item): %s",
                                    path, key, cleaned,
                                )
                        if not parent_is_service_charge:
                            found["subtotals"].append(float(cleaned))
                            logger.debug("Found subtotal at %s.%s: %s", path, key, cleaned)

            if "nm" in obj:
                nm = str(obj["nm"]).lower()
                if "service" in nm or "s. service charge" in nm:
                    for price_key in ("subtotal_price", "price", "total_price"):
                        if price_key in obj:
                            cleaned = clean_price_string(obj[price_key])
                            if cleaned:
                                found["service_charges"].append(float(cleaned))
                                logger.debug("Found service charge at %s.nm: %s", path, cleaned)
                                break

            for key, value in obj.items():
                nested = self._collect_financial_fields(value, f"{path}.{key}")
                for bucket in found:
                    found[bucket].extend(nested[bucket])

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                nested = self._collect_financial_fields(item, f"{path}[{i}]")
                for bucket in found:
                    found[bucket].extend(nested[bucket])

        return found

    def _select_subtotal(
        self,
        subtotals: List[float],
        total: Optional[str],
        tax: Optional[str],
    ) -> Optional[str]:
        """Pick the most plausible subtotal from candidates."""
        valid = [s for s in subtotals if s > MIN_VALID_SUBTOTAL]
        if not valid:
            return None

        if total and tax:
            try:
                total_num = float(total)
                reasonable = [s for s in valid if s < total_num * SUBTOTAL_TOTAL_RATIO_LIMIT]
                selected = max(reasonable) if reasonable else min(valid)
            except ValueError:
                selected = max(valid)
        else:
            selected = max(valid)

        logger.info("Selected subtotal: %s", selected)
        return str(selected)

    def _search_for_date(self, obj: Any) -> Optional[str]:
        """Recursively find the first valid date string in the CORD output."""
        if isinstance(obj, dict):
            for date_key in (
                "date", "receipt_date", "invoice_date",
                "transaction_date", "Date", "Open Time",
            ):
                if date_key in obj and validate_date(obj[date_key]):
                    return str(obj[date_key])
            for value in obj.values():
                result = self._search_for_date(value)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self._search_for_date(item)
                if result:
                    return result
        return None

    def _extract_bill_id(self, cord_json: Dict) -> Optional[str]:
        """Bill/receipt ID from known keys, rejecting price-like values."""
        for id_key in (
            "receipt_number", "invoice_no", "order_number",
            "transaction_id", "receipt_id", "Bill", "bill",
        ):
            if id_key in cord_json:
                id_str = str(cord_json[id_key]).strip()
                if id_str and not _PRICE_LIKE_ID_RE.match(id_str):
                    return id_str
        return None

    def _extract_line_items(self, cord_json: Dict) -> List[LineItemDict]:
        """Extract individual line items from the CORD 'menu' field."""
        line_items: List[LineItemDict] = []

        if "menu" not in cord_json:
            logger.info("No 'menu' field in DONUT output.")
            return line_items

        menu = cord_json["menu"]

        if isinstance(menu, list):
            for i, item in enumerate(menu):
                if not isinstance(item, dict):
                    continue

                name = item.get("nm", "")
                if not name:
                    continue
                if any(kw in name.lower() for kw in _LINE_ITEM_SKIP_KEYWORDS):
                    logger.debug("Item %d: '%s' — header row, skipping.", i, name)
                    continue

                quantity = 1
                cnt = item.get("cnt")
                if cnt:
                    try:
                        quantity = int(cnt)
                    except (ValueError, TypeError):
                        quantity = 1

                price = item.get("price")
                if not price:
                    continue
                cleaned_price = clean_price_string(price)
                if not cleaned_price:
                    logger.debug("Item %d: '%s' — price '%s' not parseable.", i, name, price)
                    continue

                price_float = float(cleaned_price)
                if not (MIN_LINE_ITEM_PRICE <= price_float <= MAX_LINE_ITEM_PRICE):
                    logger.debug("Item %d: '%s' — price %.2f out of range.", i, name, price_float)
                    continue

                unit_price = price_float
                unitprice = item.get("unitprice")
                if unitprice:
                    cleaned_unit = clean_price_string(unitprice)
                    if cleaned_unit:
                        unit_price = float(cleaned_unit)

                line_items.append(
                    LineItemDict(
                        name=name.strip(),
                        quantity=quantity,
                        unit_price=unit_price if quantity > 1 else price_float,
                        total_price=price_float,
                    )
                )

        elif isinstance(menu, dict):
            name = menu.get("nm", "")
            price = menu.get("price")
            if name and price:
                cleaned_price = clean_price_string(price)
                if cleaned_price:
                    price_float = float(cleaned_price)
                    if MIN_LINE_ITEM_PRICE < price_float < MAX_LINE_ITEM_PRICE:
                        line_items.append(
                            LineItemDict(
                                name=name.strip(),
                                quantity=1,
                                unit_price=price_float,
                                total_price=price_float,
                            )
                        )

        logger.info("Extracted %d line items.", len(line_items))
        return line_items

    def _detect_currency(self, cord_json: Dict) -> str:
        """Detect currency from symbols/codes anywhere in the CORD output."""

        def search(obj: Any) -> Optional[str]:
            if isinstance(obj, str):
                for symbol, code in CURRENCY_MAP.items():
                    if symbol in obj:
                        return code
            elif isinstance(obj, dict):
                for value in obj.values():
                    result = search(value)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = search(item)
                    if result:
                        return result
            return None

        detected = search(cord_json)
        if detected:
            logger.info("Detected currency: %s", detected)
            return detected
        logger.info("No currency symbol found; defaulting to %s.", DEFAULT_CURRENCY)
        return DEFAULT_CURRENCY

    @staticmethod
    def _get_empty_extraction() -> Dict[str, Any]:
        """Empty extraction result used when parsing fails."""
        return {
            "vendor": None,
            "date": None,
            "total": None,
            "tax": None,
            "subtotal": None,
            "bill_id": None,
            "currency": DEFAULT_CURRENCY,
            "line_items": [],
        }


_processor: Optional[ReceiptProcessor] = None
_processor_lock = threading.Lock()


def get_donut_processor(settings: Optional[Settings] = None) -> ReceiptProcessor:
    """Thread-safe lazy singleton for the DONUT processor."""
    global _processor
    if _processor is None:
        with _processor_lock:
            if _processor is None:
                logger.info("Initializing DONUT processor (first load may be slow).")
                _processor = ReceiptProcessor(settings or get_settings())
    return _processor


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

@contextmanager
def db_connection(settings: Settings) -> Iterator[sqlite3.Connection]:
    """
    Transactional connection context manager.

    Commits on success, rolls back and raises DatabaseError on any
    sqlite3 error. Always closes the connection.
    """
    conn = sqlite3.connect(str(settings.db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        logger.error("Database error — transaction rolled back: %s", exc)
        raise DatabaseError(f"Database operation failed: {exc}") from exc
    finally:
        conn.close()


def init_db(settings: Optional[Settings] = None) -> None:
    """Create all required tables/indexes if they do not exist."""
    settings = settings or get_settings()

    with db_connection(settings) as db:
        db.execute("PRAGMA journal_mode = WAL")  # Better read/write concurrency.

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                name TEXT,
                company TEXT,
                phone TEXT,
                budget REAL DEFAULT 50000.0,
                auth_method TEXT DEFAULT 'email',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS receipts (
                bill_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                vendor TEXT NOT NULL,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                tax REAL DEFAULT 0.0,
                subtotal REAL DEFAULT 0.0,
                category TEXT DEFAULT 'Uncategorized',
                currency TEXT DEFAULT 'USD',
                raw_text TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (bill_id, user_email),
                FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE
            )
            """
        )

        # Idempotent migration for legacy databases.
        try:
            db.execute("ALTER TABLE receipts ADD COLUMN currency TEXT DEFAULT 'USD'")
        except sqlite3.OperationalError:
            pass  # Column already exists.

        db.execute("CREATE INDEX IF NOT EXISTS idx_vendor ON receipts(vendor)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_date ON receipts(date)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_category ON receipts(category)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON receipts(user_email)")

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS line_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit_price REAL DEFAULT 0.0,
                total_price REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bill_id, user_email)
                    REFERENCES receipts(bill_id, user_email) ON DELETE CASCADE
            )
            """
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_line_items_receipt "
            "ON line_items(bill_id, user_email)"
        )

    logger.info("Database initialized at %s", settings.db_path)


_db_initialized = False
_db_init_lock = threading.Lock()


def ensure_db_initialized(settings: Optional[Settings] = None) -> None:
    """Run init_db exactly once per process (thread-safe)."""
    global _db_initialized
    if not _db_initialized:
        with _db_init_lock:
            if not _db_initialized:
                init_db(settings)
                _db_initialized = True


def save_receipt(
    data: ReceiptDict,
    user_email: str,
    settings: Optional[Settings] = None,
) -> None:
    """Persist a receipt header and its line items in one transaction."""
    if not user_email:
        raise ValueError("user_email is required")
    settings = settings or get_settings()

    line_items = data.get("line_items") or []

    with db_connection(settings) as db:
        db.execute(
            """
            INSERT INTO receipts
                (bill_id, user_email, vendor, date, amount, tax, subtotal,
                 category, currency, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["bill_id"],
                user_email,
                data["vendor"],
                data["date"],
                float(data["amount"]),
                float(data.get("tax") or 0.0),
                float(data.get("subtotal") or 0.0),
                data.get("category") or DEFAULT_CATEGORY,
                data.get("currency") or DEFAULT_CURRENCY,
                data.get("raw_text"),
            ),
        )

        if line_items:
            db.executemany(
                """
                INSERT INTO line_items
                    (bill_id, user_email, item_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        data["bill_id"],
                        user_email,
                        item.get("name", "Unknown Item"),
                        int(item.get("quantity", 1)),
                        float(item.get("unit_price", 0.0)),
                        float(item.get("total_price", 0.0)),
                    )
                    for item in line_items
                ],
            )

    logger.info(
        "Saved receipt %s with %d line items for %s.",
        data["bill_id"], len(line_items), user_email,
    )


def check_receipt_duplicate(
    bill_id: str,
    vendor: str,
    date: str,
    amount: float,
    user_email: str,
    settings: Optional[Settings] = None,
) -> bool:
    """
    Duplicate detection:
      1. Exact bill_id match (auto-generated REC-* IDs excluded).
      2. Fuzzy match: same vendor + date + amount (±0.01).
    """
    settings = settings or get_settings()

    with db_connection(settings) as db:
        if bill_id and len(bill_id) > 2 and not bill_id.startswith(AUTOGEN_ID_PREFIX):
            cur = db.execute(
                "SELECT 1 FROM receipts WHERE bill_id = ? AND user_email = ?",
                (bill_id, user_email),
            )
            if cur.fetchone():
                return True

        cur = db.execute(
            """
            SELECT 1 FROM receipts
            WHERE vendor = ? AND date = ?
              AND ABS(amount - ?) < 0.01 AND user_email = ?
            """,
            (vendor, date, float(amount), user_email),
        )
        return cur.fetchone() is not None


def receipt_exists(
    bill_id: str, user_email: str, settings: Optional[Settings] = None
) -> bool:
    """Check whether a receipt exists for this user."""
    settings = settings or get_settings()
    with db_connection(settings) as db:
        cur = db.execute(
            "SELECT 1 FROM receipts WHERE bill_id = ? AND user_email = ?",
            (bill_id, user_email),
        )
        return cur.fetchone() is not None


def fetch_all_receipts(
    user_email: str, settings: Optional[Settings] = None
) -> List[Dict[str, Any]]:
    """All receipts for a user, newest first."""
    if not user_email:
        raise ValueError("user_email is required")
    settings = settings or get_settings()

    with db_connection(settings) as db:
        cur = db.execute(
            """
            SELECT bill_id, vendor, date, amount, tax, subtotal, category
            FROM receipts WHERE user_email = ? ORDER BY date DESC
            """,
            (user_email,),
        )
        return [_row_to_dict(row) for row in cur.fetchall()]


def get_receipt_by_id(
    bill_id: str, user_email: str, settings: Optional[Settings] = None
) -> Optional[Dict[str, Any]]:
    """Fetch one receipt by ID, or None."""
    settings = settings or get_settings()
    with db_connection(settings) as db:
        cur = db.execute(
            "SELECT * FROM receipts WHERE bill_id = ? AND user_email = ?",
            (bill_id, user_email),
        )
        row = cur.fetchone()
        return _row_to_dict(row) if row else None


_UPDATABLE_RECEIPT_FIELDS = frozenset(
    {"vendor", "date", "amount", "tax", "subtotal", "category"}
)


def update_receipt(
    bill_id: str,
    update_data: Dict[str, Any],
    user_email: str,
    settings: Optional[Settings] = None,
) -> bool:
    """
    Update whitelisted receipt fields. Column names come only from the
    whitelist (never user input); values are always parameterized.
    """
    settings = settings or get_settings()

    fields, values = [], []
    for key, value in update_data.items():
        if key in _UPDATABLE_RECEIPT_FIELDS and value is not None:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    values.extend([bill_id, user_email])
    query = (
        f"UPDATE receipts SET {', '.join(fields)} "
        "WHERE bill_id = ? AND user_email = ?"
    )

    with db_connection(settings) as db:
        cur = db.execute(query, values)
        return cur.rowcount > 0


def search_receipts(
    user_email: str,
    vendor: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    settings: Optional[Settings] = None,
) -> List[Dict[str, Any]]:
    """Dynamic filtered search across a user's receipts."""
    if not user_email:
        raise ValueError("user_email is required")
    settings = settings or get_settings()

    query = "SELECT * FROM receipts WHERE user_email = ?"
    params: List[Any] = [user_email]

    if vendor:
        query += " AND vendor LIKE ?"
        params.append(f"%{vendor}%")
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if min_amount is not None:
        query += " AND amount >= ?"
        params.append(float(min_amount))
    if max_amount is not None:
        query += " AND amount <= ?"
        params.append(float(max_amount))

    query += " ORDER BY date DESC"

    with db_connection(settings) as db:
        cur = db.execute(query, params)
        return [_row_to_dict(row) for row in cur.fetchall()]


def delete_receipt(
    bill_id: str, user_email: str, settings: Optional[Settings] = None
) -> bool:
    """Delete one receipt (line items cascade). Returns True if deleted."""
    settings = settings or get_settings()
    with db_connection(settings) as db:
        cur = db.execute(
            "DELETE FROM receipts WHERE bill_id = ? AND user_email = ?",
            (bill_id, user_email),
        )
        return cur.rowcount > 0


def clear_all_receipts(
    user_email: str, settings: Optional[Settings] = None
) -> int:
    """Delete all receipts for a user. Returns number deleted."""
    settings = settings or get_settings()
    with db_connection(settings) as db:
        cur = db.execute("DELETE FROM receipts WHERE user_email = ?", (user_email,))
        return cur.rowcount


def get_user_by_email(
    email: str, settings: Optional[Settings] = None
) -> Optional[Dict[str, Any]]:
    """Fetch a user row by email, or None."""
    settings = settings or get_settings()
    with db_connection(settings) as db:
        cur = db.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_user(
    email: str,
    password_hash: str,
    name: str = "",
    company: str = "",
    phone: str = "",
    auth_method: str = "email",
    settings: Optional[Settings] = None,
) -> Dict[str, Any]:
    """Create a user and return the created row."""
    settings = settings or get_settings()
    with db_connection(settings) as db:
        db.execute(
            """
            INSERT INTO users (email, password_hash, name, company, phone, auth_method)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (email, password_hash, name, company, phone, auth_method),
        )
    user = get_user_by_email(email, settings)
    if user is None:  # pragma: no cover - defensive
        raise DatabaseError(f"User creation failed for {email}")
    return user


def update_user_budget(
    email: str, budget: float, settings: Optional[Settings] = None
) -> None:
    """Update a user's monthly budget."""
    settings = settings or get_settings()
    with db_connection(settings) as db:
        db.execute("UPDATE users SET budget = ? WHERE email = ?", (budget, email))


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Normalize a receipts row into a stable dict shape."""
    data = dict(row)
    return {
        "bill_id": data.get("bill_id"),
        "vendor": data.get("vendor"),
        "date": data.get("date"),
        "amount": float(data.get("amount") or 0.0),
        "tax": float(data.get("tax") or 0.0),
        "subtotal": float(data.get("subtotal") or 0.0),
        "category": data.get("category") or DEFAULT_CATEGORY,
    }


# ============================================================================
# MAIN PROCESSING PIPELINE
# ============================================================================

def _load_image(
    file_bytes: bytes, file_type: FileType, settings: Settings
) -> Image.Image:
    """Load the first page/frame of an upload as a PIL Image."""
    if file_type is FileType.PDF:
        tmp_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = Path(tmp.name)
            pages = pdf_to_images(tmp_path, dpi=settings.pdf_dpi)
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

        if not pages:
            raise OCRProcessingError("Could not render any pages from the PDF.")
        return pages[0]

    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.load()  # Force decode now so corrupt files fail here, not later.
        return image
    except UnidentifiedImageError as exc:
        raise OCRProcessingError(f"Cannot identify image content: {exc}") from exc
    except Exception as exc:
        raise OCRProcessingError(f"Could not read uploaded file: {exc}") from exc


def _build_receipt_dict(extracted: Dict[str, Any]) -> ReceiptDict:
    """Clean and normalize raw DONUT output into the final ReceiptDict."""
    vendor = (extracted.get("vendor") or "Unknown Vendor").strip()
    date_str = extracted.get("date")
    bill_id = extracted.get("bill_id")

    amount = clean_amount(extracted.get("total"))
    tax = clean_amount(extracted.get("tax")) or 0.0
    subtotal = clean_amount(extracted.get("subtotal")) or 0.0

    parsed_date = clean_date(date_str) if date_str else None
    date_out = (
        parsed_date.isoformat()
        if isinstance(parsed_date, date_cls)
        else (date_str or date_cls.today().isoformat())
    )

    if not bill_id or not str(bill_id).strip():
        bill_id = f"{AUTOGEN_ID_PREFIX}{uuid.uuid4().hex[:10].upper()}"

    if amount is not None and not subtotal:
        subtotal = max(0.0, amount - tax)

    if amount is None:
        logger.warning("No total amount extracted; defaulting to 0.0.")

    return ReceiptDict(
        bill_id=bill_id,
        vendor=vendor,
        date=date_out,
        amount=amount if amount is not None else 0.0,
        tax=tax,
        subtotal=subtotal if subtotal else (amount if amount is not None else 0.0),
        category=guess_category(vendor),
        currency=extracted.get("currency", DEFAULT_CURRENCY),
        raw_text="",
        line_items=extracted.get("line_items", []),
    )


def process_receipt_file(
    file_bytes: bytes,
    filename: str,
    *,
    settings: Optional[Settings] = None,
) -> ReceiptDict:
    """
    Full extraction pipeline: raw file bytes -> structured receipt dict.

    Raises:
        FileValidationError: Invalid file (size, extension, or content).
        OCRProcessingError: File could not be rendered/decoded.
        DONUTError: Model inference failed.
    """
    settings = settings or get_settings()

    # 1. Validate (size, extension, magic bytes).
    file_type = validate_upload(file_bytes, filename, settings)

    # 2. Load image (PDF first page or direct decode).
    image = _load_image(file_bytes, file_type, settings)

    # 3. Optimize for OCR if oversized.
    info = get_image_info(image)
    logger.info(
        "Original image: %dx%d (%.2fMP)", info["width"], info["height"], info["megapixels"]
    )
    if info["megapixels"] > settings.image_optimize_threshold_mp:
        image = optimize_image_for_ocr(image, max_dimension=settings.max_image_dimension)
        opt = get_image_info(image)
        logger.info(
            "Optimized to: %dx%d (%.2fMP)", opt["width"], opt["height"], opt["megapixels"]
        )

    # 4. Extract with DONUT.
    try:
        processor = get_donut_processor(settings)
        extracted = processor.extract_receipt_data(image)
    except DONUTError:
        raise
    except Exception as exc:
        raise OCRProcessingError(
            f"Unexpected error during receipt processing: {exc}"
        ) from exc

    # 5. Clean, normalize, and return.
    result = _build_receipt_dict(extracted)
    logger.info(
        "Parsed receipt: vendor=%s amount=%s currency=%s line_items=%d",
        result["vendor"], result["amount"], result["currency"], len(result["line_items"]),
    )
    return result


def process_and_store_receipt(
    file_bytes: bytes,
    filename: str,
    user_email: str,
    *,
    settings: Optional[Settings] = None,
    allow_duplicate: bool = False,
) -> ReceiptDict:
    """
    Complete pipeline: validate -> extract -> duplicate-check -> store.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename: Original filename (used for extension validation).
        user_email: Owner of the receipt (required for storage).
        settings: Optional override; defaults to env-based singleton.
        allow_duplicate: If True, skip duplicate detection and force insert.

    Returns:
        The extracted and stored ReceiptDict.

    Raises:
        FileValidationError / OCRProcessingError / DONUTError: Extraction failures.
        DuplicateReceiptError: Receipt already exists for this user.
        DatabaseError: Storage failed (transaction rolled back).
    """
    if not user_email:
        raise ValueError("user_email is required")
    settings = settings or get_settings()

    ensure_db_initialized(settings)

    result = process_receipt_file(file_bytes, filename, settings=settings)

    if not allow_duplicate and check_receipt_duplicate(
        result["bill_id"],
        result["vendor"],
        result["date"],
        result["amount"],
        user_email,
        settings,
    ):
        logger.warning(
            "Duplicate receipt rejected: bill_id=%s vendor=%s user=%s",
            result["bill_id"], result["vendor"], user_email,
        )
        raise DuplicateReceiptError(
            f"Receipt already exists (bill_id={result['bill_id']}, "
            f"vendor={result['vendor']}, date={result['date']}, "
            f"amount={result['amount']})."
        )

    save_receipt(result, user_email, settings)
    logger.info("Receipt processed and stored: %s", result["bill_id"])
    return result


# ============================================================================
# CLI ENTRYPOINT
# ============================================================================

def _cli() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Extract structured data from a receipt image/PDF."
    )
    parser.add_argument("file", type=Path, help="Path to receipt image or PDF")
    parser.add_argument("--email", default="cli@example.com", help="Owner email")
    parser.add_argument(
        "--no-store", action="store_true", help="Extract only; skip database storage"
    )
    parser.add_argument(
        "--allow-duplicate", action="store_true", help="Bypass duplicate detection"
    )
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"Error: file not found: {args.file}")
        return 1

    file_bytes = args.file.read_bytes()

    try:
        if args.no_store:
            result = process_receipt_file(file_bytes, args.file.name)
        else:
            result = process_and_store_receipt(
                file_bytes,
                args.file.name,
                args.email,
                allow_duplicate=args.allow_duplicate,
            )
    except ReceiptExtractionError as exc:
        print(f"Extraction failed: {exc}")
        return 2

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())