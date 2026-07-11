import cv2
import numpy as np
from PIL import Image
from typing import cast

def preprocess_image(pil_image: Image.Image, mode: str = "simple") -> Image.Image:
    """
    Multi-stage preprocessing for receipts.
    Modes:
      - 'simple': Basic grayscale, contrast normalization, and sharpening.
      - 'advanced': Deskewing, Resizing, and Adaptive Thresholding.
    """
    img = np.array(pil_image.convert("L"))

    if mode == "advanced":
        # Deskewing
        coords = np.column_stack(np.where(img > 0))
        if coords.size > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        # Resizing (upscale for better OCR if too small)
        (h, w) = img.shape[:2]
        if w < 1000:
            scale = 1000 / w
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Adaptive Thresholding
        img = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        img = cv2.medianBlur(img, 3)
    else:
        # Simple mode: Contrast and Sharpen
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        img = cv2.filter2D(img, -1, kernel)

    return Image.fromarray(img)