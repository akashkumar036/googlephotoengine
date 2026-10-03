from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt
from app.config import get_settings

settings = get_settings()


def hash_password(plain: str) -> str:
    """Hash password using bcrypt directly (Python 3.12 compatible)."""
    pw_bytes = plain.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        pw_bytes = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
    except Exception:
        return False


def _create_token(data: dict, expires_in_seconds: int) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_access_token(user_id: str, role: str) -> str:
    return _create_token(
        {"sub": user_id, "role": role, "type": "access"},
        settings.jwt_access_expiry,
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        {"sub": user_id, "type": "refresh"},
        settings.jwt_refresh_expiry,
    )


def decode_token(token: str) -> dict:
    """Raises JWTError on invalid / expired token."""
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
