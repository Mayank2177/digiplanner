"""
security.py — NEW MODULE.

This did not exist in the original codebase at all. Login/Signup pages in
the React frontend had nothing real to call, and the `users` table stored
plaintext passwords with no session/token mechanism.

This module adds:
  - bcrypt password hashing (via the `bcrypt` package directly — NOT
    `passlib`. passlib 1.7.4's bcrypt handler has a known incompatibility
    with modern bcrypt releases that raises
    `ValueError: password cannot be longer than 72 bytes` on the very
    first hash call, even for short passwords. Using `bcrypt` directly
    avoids that landmine entirely.)
  - JWT issuing + verification (via PyJWT)
  - a `get_current_user_email` FastAPI dependency that every protected
    route uses to find out "who is calling", replacing the old (broken)
    reliance on Streamlit's st.session_state.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

bearer_scheme = HTTPBearer(auto_error=False)

# bcrypt has a hard 72-byte input limit; truncate defensively so unusually
# long passwords fail cleanly instead of raising inside the bcrypt library.
_MAX_PASSWORD_BYTES = 72


def _prep(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_PASSWORD_BYTES]


# ================= PASSWORD HASHING =================
def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(_prep(plain_password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_prep(plain_password), password_hash.encode("utf-8"))
    except Exception:
        return False


# ================= JWT TOKENS =================
def create_access_token(user_email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": user_email, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Returns the user_email (subject) if the token is valid, else None."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ================= FASTAPI DEPENDENCY =================
def get_current_user_email(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """
    Use as a route dependency:

        @app.get("/api/v1/receipts")
        def get_receipts(user_email: str = Depends(get_current_user_email)):
            ...

    Expects the frontend to send:  Authorization: Bearer <token>
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Include 'Authorization: Bearer <token>' header.",
        )

    user_email = decode_access_token(credentials.credentials)
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
        )
    return user_email
