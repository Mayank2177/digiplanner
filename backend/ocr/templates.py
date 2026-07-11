"""
paddle_engine.py — Thread-safe PaddleOCR text extraction engine.

Fixes applied:
  - Thread-safe singleton with double-checked locking.
  - Tracks init failures to avoid infinite retry loops.
  - Supports multiple languages and angle classification.
  - Proper exception propagation with custom exception types.
"""

import threading
import numpy as np
from PIL import Image
from typing import Optional, List

# ─── Module-level state ─────────────────────────────────────────────────────
_paddle_engine: Optional[object] = None
_paddle_lock = threading.Lock()
_paddle_init_failed = False
_paddle_init_error: Optional[Exception] = None


class PaddleOCRError(Exception):
    """Raised when PaddleOCR initialization or inference fails."""
    pass


def _get_paddle_engine(
    lang: str = "en",
    use_angle_cls: bool = True,
    show_log: bool = False,
    use_gpu: bool = False,
) -> object:
    """
    Get or initialize the PaddleOCR engine (thread-safe singleton).

    Uses double-checked locking pattern for thread safety without
    holding the lock on every call after initialization.

    Args:
        lang: Language code ("en", "ch", "fr", etc.).
        use_angle_cls: Enable rotation angle classification.
        show_log: Show PaddleOCR internal logs.
        use_gpu: Use GPU for inference (if available).

    Returns:
        Initialized PaddleOCR instance.

    Raises:
        PaddleOCRError: If PaddleOCR is not installed or init fails.
    """
    global _paddle_engine, _paddle_init_failed, _paddle_init_error

    # Fast path: already initialized
    if _paddle_engine is not None:
        return _paddle_engine

    # If we already failed, don't retry indefinitely
    if _paddle_init_failed:
        raise PaddleOCRError(
            f"PaddleOCR initialization previously failed: {_paddle_init_error}"
        )

    # Slow path: acquire lock and initialize
    with _paddle_lock:
        # Double-check after acquiring lock
        if _paddle_engine is not None:
            return _paddle_engine

        if _paddle_init_failed:
            raise PaddleOCRError(
                f"PaddleOCR initialization previously failed: {_paddle_init_error}"
            )

        try:
            from paddleocr import PaddleOCR
        except ImportError as e:
            _paddle_init_failed = True
            _paddle_init_error = e
            raise PaddleOCRError(
                "PaddleOCR is not installed. Install with: pip install paddleocr"
            ) from e

        try:
            _paddle_engine = PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang=lang,
                show_log=show_log,
                use_gpu=use_gpu,
            )
        except Exception as e:
            _paddle_init_failed = True
            _paddle_init_error = e
            raise PaddleOCRError(f"Failed to initialize PaddleOCR: {e}") from e

    return _paddle_engine


def reset_paddle_engine() -> None:
    """
    Reset the PaddleOCR engine singleton.

    Call this if you need to reinitialize with different parameters
    (e.g., different language) or if the engine becomes corrupted.
    """
    global _paddle_engine, _paddle_init_failed, _paddle_init_error
    with _paddle_lock:
        _paddle_engine = None
        _paddle_init_failed = False
        _paddle_init_error = None


def extract_text_paddle(
    pil_image: Image.Image,
    lang: str = "en",
    confidence_threshold: float = 0.0,
) -> str:
    """
    Extract text from an image using PaddleOCR.

    Args:
        pil_image: Input PIL Image.
        lang: Language code for OCR model.
        confidence_threshold: Minimum confidence score (0-1) for text lines.
            Lines below this threshold are discarded. 0 = keep all.

    Returns:
        Extracted text as a single string with newline-separated lines.
        Returns empty string if no text is detected.

    Raises:
        PaddleOCRError: If OCR engine fails to initialize or inference fails.
        ValueError: If input image is invalid.
    """
    if pil_image is None:
        raise ValueError("Input image cannot be None")

    # Ensure RGB for PaddleOCR
    img_array = np.array(pil_image.convert("RGB"))

    if img_array.size == 0:
        return ""

    engine = _get_paddle_engine(lang=lang)

    try:
        result = engine.ocr(img_array, cls=True)
    except Exception as e:
        raise PaddleOCRError(f"PaddleOCR inference failed: {e}") from e

    if not result or not result[0]:
        return ""

    full_text: List[str] = []
    for line in result[0]:
        # line format: [[coords], (text, confidence)]
        text, confidence = line[1][0], line[1][1]
        if confidence_threshold > 0 and confidence < confidence_threshold:
            continue
        if text and text.strip():
            full_text.append(text.strip())

    return "\n".join(full_text)


def extract_text_with_boxes(
    pil_image: Image.Image,
    lang: str = "en",
) -> List[dict]:
    """
    Extract text with bounding box coordinates from an image.

    Args:
        pil_image: Input PIL Image.
        lang: Language code.

    Returns:
        List of dicts with keys: 'text', 'confidence', 'box' (list of 4 points).
    """
    if pil_image is None:
        raise ValueError("Input image cannot be None")

    img_array = np.array(pil_image.convert("RGB"))
    engine = _get_paddle_engine(lang=lang)

    try:
        result = engine.ocr(img_array, cls=True)
    except Exception as e:
        raise PaddleOCRError(f"PaddleOCR inference failed: {e}") from e

    if not result or not result[0]:
        return []

    output = []
    for line in result[0]:
        box, (text, confidence) = line[0], line[1]
        output.append({
            "text": text.strip(),
            "confidence": confidence,
            "box": box,
        })

    return output
