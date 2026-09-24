import os
import platform
from dotenv import load_dotenv

load_dotenv()  # loads variables from a .env file in the backend/ folder if present

# =========================================================
# APPLICATION
# =========================================================
APP_TITLE = os.getenv("APP_TITLE", "Receipt Vault & Analyzer")
APP_VERSION = "2.0.0"

# =========================================================
# BASE DIRECTORY
# =========================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =========================================================
# DATABASE CONFIGURATION (SQLite)
# =========================================================
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.getenv("DB_PATH", os.path.join(DATA_DIR, "receipts.db"))

# =========================================================
# AUTH / SECURITY
# =========================================================
# IMPORTANT: set a real, random secret in your .env in production.
# e.g. generate one with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours

# =========================================================
# CORS — allowed frontend origins
# =========================================================
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

# =========================================================
# DONUT MODEL CONFIGURATION
# =========================================================
# DONUT (Document Understanding Transformer) replaces traditional OCR
DONUT_MODEL = os.getenv("DONUT_MODEL", "naver-clova-ix/donut-base-finetuned-docvqa")
DONUT_DEVICE = int(os.getenv("DONUT_DEVICE", "-1"))  # -1 for CPU, 0 for GPU

# =========================================================
# FILE UPLOAD CONFIGURATION
# =========================================================
ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "pdf"]
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================================================
# IMAGE PROCESSING CONFIGURATION
# =========================================================
IMAGE_DPI = 300
GRAYSCALE = True

# =========================================================
# ANALYTICS CONFIGURATION
# =========================================================
CURRENCY_SYMBOL = "$"

# =========================================================
# EMAIL / SMS ALERTS (optional — alerts are skipped gracefully if unset)
# =========================================================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")


def is_windows() -> bool:
    return os.name == "nt"
