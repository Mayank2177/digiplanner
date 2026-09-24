"""
Image Optimization Module

Resizes and optimizes images before DONUT processing to reduce inference time.
"""

from PIL import Image
from typing import Tuple


def optimize_image_for_ocr(image: Image.Image, max_dimension: int = 1280) -> Image.Image:
    """
    Optimize image for OCR processing:
    - Resize to reasonable dimensions (DONUT works well with 1280px max)
    - Convert to RGB
    - Maintain aspect ratio
    
    Args:
        image: PIL Image
        max_dimension: Maximum width or height (default 1280px)
    
    Returns:
        Optimized PIL Image
    """
    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    # Get current dimensions
    width, height = image.size
    
    # Check if resizing is needed
    if width <= max_dimension and height <= max_dimension:
        return image
    
    # Calculate new dimensions maintaining aspect ratio
    if width > height:
        new_width = max_dimension
        new_height = int((max_dimension / width) * height)
    else:
        new_height = max_dimension
        new_width = int((max_dimension / height) * width)
    
    # Resize using high-quality Lanczos filter
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return resized


def get_image_info(image: Image.Image) -> dict:
    """Get image information for logging."""
    return {
        "size": image.size,
        "mode": image.mode,
        "width": image.width,
        "height": image.height,
        "megapixels": round((image.width * image.height) / 1_000_000, 2)
    }
