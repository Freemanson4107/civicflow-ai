"""
Security core.

Design choices (documented for the demo/judges):
- Passwords hashed with bcrypt (via passlib), cost factor 12 — never stored
  or logged in plaintext.
- Access tokens: short-lived (15 min) JWT, signed HS256.
- Refresh tokens: long-lived (7 days), stored hashed in DB, rotated on
  every use (old refresh token invalidated -> mitigates token replay).
- Account lockout: 5 failed login attempts -> 15 min lockout per account,
  mitigates brute-force/credential-stuffing.
- All tokens carry a `jti` (unique id) so individual sessions can be revoked.
"""
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


# ---------- Password handling ----------
def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def password_meets_policy(password: str) -> tuple[bool, str]:
    """Enforced server-side regardless of what the frontend checks."""
    if len(password) < 10:
        return False, "Password must be at least 10 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in password):
        return False, "Password must contain at least one special character."
    return True, ""


# ---------- JWT handling ----------
def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({
        "iat": now,
        "exp": now + expires_delta,
        "jti": secrets.token_hex(16),
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, role: str = "citizen") -> str:
    return _create_token(
        {"sub": user_id, "role": role, "type": "access"},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        {"sub": user_id, "type": "refresh"},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def hash_refresh_token(token: str) -> str:
    """Store only a SHA-256 hash of the refresh token in DB, never the raw token."""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid or expired token: {e}")


# ---------- Account lockout helpers ----------
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def is_locked_out(failed_attempts: int, last_failed_at: datetime | None) -> bool:
    if failed_attempts < MAX_FAILED_ATTEMPTS:
        return False
    if last_failed_at is None:
        return False
    return datetime.now(timezone.utc) < last_failed_at.replace(tzinfo=timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
