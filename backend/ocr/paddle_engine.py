import numpy as np
from PIL import Image
try:
    from paddleocr import PaddleOCR
    # Initialize PaddleOCR (using CPU by default for portability)
    # This will download models on first run
    _paddle_engine = None
except ImportError:
    _paddle_engine = None

def extract_text_paddle(pil_image: Image.Image) -> str:
    """
    Extracts text from an image using PaddleOCR.
    """
    global _paddle_engine
    
    try:
        if _paddle_engine is None:
            # lang='en' for English, use_angle_cls=True for rotation correction
            _paddle_engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        
        # Convert PIL to numpy array
        img_array = np.array(pil_image.convert("RGB"))
        
        # PaddleOCR returns a list of results
        result = _paddle_engine.ocr(img_array, cls=True)
        
        if not result or not result[0]:
            return ""
            
        full_text = []
        for line in result[0]:
            # Each line is [[coords], (text, confidence)]
            text = line[1][0]
            full_text.append(text)
            
        return "\n".join(full_text)
    except Exception as e:
        print(f"PaddleOCR Error: {e}")
        return ""
