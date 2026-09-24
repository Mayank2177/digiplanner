"""
validators.py — File and data validation helpers.

FIX APPLIED: the original version was written for Streamlit's
`st.file_uploader` return object (`uploaded_file.name`, `uploaded_file.size`
attributes). FastAPI's `UploadFile` doesn't expose `.size` the same way and
this backend no longer uses Streamlit at all, so this now validates a
filename + raw byte length directly — usable from any web framework.
"""

from config.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB


def validate_uploaded_file(filename: str, file_size_bytes: int) -> None:
    """
    Raises ValueError if the file extension isn't allowed or the file is
    too large. Call this in the upload endpoint before running OCR.
    """
    if not filename:
        raise ValueError("No file uploaded")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Invalid file type '.{ext}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size_bytes > max_bytes:
        raise ValueError(f"File size exceeds the {MAX_FILE_SIZE_MB}MB limit")


def is_valid_email(email: str) -> bool:
    """Lightweight email format check (no external dependency required)."""
    import re
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))
