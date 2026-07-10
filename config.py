
import os
import platform
import pytesseract


# =========================================================
# APPLICATION CONFIGURATION
# =========================================================
APP_TITLE = "Mydigibill"

# =========================================================
# BASE DIRECTORY
# =========================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =========================================================
# DATABASE CONFIGURATION (SQLite)
# =========================================================
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "receipts.db")
os.makedirs(DATA_DIR, exist_ok=True)

# =========================================================
# OCR CONFIGURATION
# =========================================================
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH")
    poppler_path = os.getenv("POPPLER_PATH")
else:
    None


# =========================================================
# FILE UPLOAD CONFIGURATION
# =========================================================
ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "pdf"]
MAX_FILE_SIZE_MB = 10

# =========================================================
# IMAGE PROCESSING CONFIGURATION
# =========================================================
IMAGE_DPI = 300
GRAYSCALE = True

# =========================================================
# ANALYTICS CONFIGURATION
# =========================================================
CURRENCY_SYMBOL = "₹"

def is_windows():
    return os.name == "nt"