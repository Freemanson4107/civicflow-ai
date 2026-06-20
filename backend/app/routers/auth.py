from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import (
    hash_password, verify_password, password_meets_policy,
    create_access_token, create_refresh_token, hash_refresh_token,
    decode_token, is_locked_out, MAX_FAILED_ATTEMPTS,
)
from app.models.orm_models import User, RefreshToken
from app.models.schemas import SignupRequest, LoginRequest, TokenResponse, RefreshRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        # Generic message — do not reveal whether the email exists (enumeration protection)
        raise HTTPException(status_code=400, detail="Unable to create account with provided details.")

    ok, msg = password_meets_policy(payload.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        region=payload.region,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _issue_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    # Constant-shape response whether or not user exists, to reduce enumeration/timing leaks
    generic_error = HTTPException(status_code=401, detail="Invalid email or password.")

    if not user:
        raise generic_error

    if is_locked_out(user.failed_login_attempts, user.last_failed_login_at):
        raise HTTPException(
            status_code=429,
            detail="Account temporarily locked due to multiple failed login attempts. Try again in 15 minutes.",
        )

    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        user.last_failed_login_at = datetime.now(timezone.utc)
        db.commit()
        raise generic_error

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled.")

    # success — reset lockout counters
    user.failed_login_attempts = 0
    user.last_failed_login_at = None
    db.commit()

    return _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        claims = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

    if claims.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type.")

    token_hash = hash_refresh_token(payload.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if not stored or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token is no longer valid.")

    user = db.query(User).filter(User.id == claims["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive.")

    # Rotate: revoke old, issue new (prevents replay of stolen refresh tokens)
    stored.revoked = True
    db.commit()

    return _issue_tokens(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if stored:
        stored.revoked = True
        db.commit()
    return


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    access_token = create_access_token(user.id, role=user.role)
    refresh_token = create_refresh_token(user.id)

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
