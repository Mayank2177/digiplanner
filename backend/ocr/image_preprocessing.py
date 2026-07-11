"""
image_preprocessing.py — Receipt image preprocessing pipeline.

Fixes applied:
  - Deskewing: Replaced broken minAreaRect with Hough Line Transform projection profile.
  - Sharpening: Fixed uint8 overflow by converting to float32 before kernel application.
  - Added denoising, border removal, and adaptive preprocessing.
  - Added proper type hints and docstrings.
"""

import cv2
import numpy as np
from PIL import Image
from typing import Literal


def preprocess_image(
    pil_image: Image.Image,
    mode: Literal["simple", "advanced"] = "simple"
) -> Image.Image:
    """
    Multi-stage preprocessing for receipt images to improve OCR accuracy.

    Modes:
      - 'simple':  Grayscale, contrast normalization, denoising, sharpening.
      - 'advanced': Deskewing, resizing, adaptive thresholding, morphological cleanup.

    Args:
        pil_image: Input PIL Image (any mode).
        mode: Preprocessing pipeline to use.

    Returns:
        Preprocessed PIL Image in grayscale ("L").
    """
    # Convert to grayscale numpy array
    img = np.array(pil_image.convert("L"))

    if mode == "advanced":
        # ── Step 1: Denoise before any transforms ─────────────────────────
        img = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)

        # ── Step 2: Deskew using Hough Line Transform ──────────────────────
        img = _deskew_hough(img, max_angle=15.0)

        # ── Step 3: Remove black borders (common in scanned receipts) ──────
        img = _remove_borders(img)

        # ── Step 4: Resize if too small (OCR needs ~300 DPI equivalent) ──
        (h, w) = img.shape[:2]
        if w < 1200:
            scale = 1200 / w
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # ── Step 5: Adaptive Gaussian Thresholding ─────────────────────────
        # Bilateral filter first to reduce noise while preserving edges
        img = cv2.bilateralFilter(img, 9, 75, 75)
        img = cv2.adaptiveThreshold(
            img, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            15,  # blockSize: larger = smoother
            10   # C: subtracted from mean
        )

        # ── Step 6: Morphological cleanup ──────────────────────────────────
        # Remove salt-and-pepper noise
        img = cv2.medianBlur(img, 3)

        # Small opening to remove isolated dots
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

    else:
        # ═══════════════════════════════════════════════════════════════
        # SIMPLE MODE
        # ═══════════════════════════════════════════════════════════════

        # Normalize contrast
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

        # Denoise
        img = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)

        # Sharpen using float32 to prevent uint8 overflow/underflow
        kernel = np.array([[-1, -1, -1],
                           [-1,  9, -1],
                           [-1, -1, -1]], dtype=np.float32)
        img_f = img.astype(np.float32)
        img_f = cv2.filter2D(img_f, -1, kernel)
        img = np.clip(img_f, 0, 255).astype(np.uint8)

    return Image.fromarray(img)


def _deskew_hough(img: np.ndarray, max_angle: float = 15.0) -> np.ndarray:
    """
    Deskew an image using the Hough Line Transform.

    Detects near-horizontal lines, computes their angles, and rotates
    the image by the median angle.

    Args:
        img: Grayscale numpy array.
        max_angle: Maximum absolute angle to correct (degrees).

    Returns:
        Deskewed image.
    """
    # Edge detection
    edges = cv2.Canny(img, 50, 150, apertureSize=3)

    # Detect lines using probabilistic Hough transform
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180,
        threshold=100,
        minLineLength=max(img.shape[1] // 4, 100),
        maxLineGap=20
    )

    if lines is None or len(lines) == 0:
        return img  # No lines found, assume already straight

    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        # Avoid division by zero for vertical lines
        if abs(x2 - x1) < 1e-6:
            continue
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        # Only consider near-horizontal lines
        if abs(angle) < max_angle:
            angles.append(angle)

    if not angles:
        return img

    # Use median angle (robust to outliers)
    median_angle = np.median(angles)

    # Only rotate if angle is significant
    if abs(median_angle) < 0.5:
        return img

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)

    # Compute new bounding box to avoid cropping
    cos = abs(M[0, 0])
    sin = abs(M[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)

    # Adjust rotation matrix for the new center
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]

    deskewed = cv2.warpAffine(
        img, M, (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255  # White background
    )
    return deskewed


def _remove_borders(img: np.ndarray, threshold: int = 250) -> np.ndarray:
    """
    Remove black borders around a scanned receipt.

    Finds the bounding box of non-white content and crops to it.

    Args:
        img: Grayscale image.
        threshold: Pixel value below which is considered content.

    Returns:
        Cropped image.
    """
    # Binary mask: content pixels
    _, binary = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY_INV)

    # Find contours of content
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return img

    # Get bounding box of all content
    x_min, y_min, x_max, y_max = float('inf'), float('inf'), 0, 0
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if area < 100:  # Ignore tiny noise blobs
            continue
        x_min = min(x_min, x)
        y_min = min(y_min, y)
        x_max = max(x_max, x + w)
        y_max = max(y_max, y + h)

    # Add small padding
    pad = 10
    x_min = max(0, x_min - pad)
    y_min = max(0, y_min - pad)
    x_max = min(img.shape[1], x_max + pad)
    y_max = min(img.shape[0], y_max + pad)

    if x_max <= x_min or y_max <= y_min:
        return img

    return img[y_min:y_max, x_min:x_max]
