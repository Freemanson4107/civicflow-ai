from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.orm_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    try:
        claims = decode_token(token)
    except ValueError:
        raise credentials_error

    if claims.get("type") != "access":
        raise credentials_error

    user = db.query(User).filter(User.id == claims.get("sub")).first()
    if not user or not user.is_active:
        raise credentials_error
    return user


def get_current_user_optional(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User | None:
    """For endpoints usable by anonymous visitors (e.g. public demo) but
    personalized when a valid token is present."""
    if not token:
        return None
    try:
        claims = decode_token(token)
        if claims.get("type") != "access":
            return None
        return db.query(User).filter(User.id == claims.get("sub")).first()
    except ValueError:
        return None
