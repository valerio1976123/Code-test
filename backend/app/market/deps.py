from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import _bearer_from_auth_header
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.security.jwt import safe_decode_token
from app.security.passwords import hash_password


def get_market_user(db: Session = Depends(get_db), authorization: str | None = Header(default=None)) -> User:
    """
    Market endpoints are usable without auth in dev mode.

    - If a valid Bearer access token is provided, that user is used.
    - Otherwise (dev mode), we auto-create/use a deterministic "demo" user.
    """
    token = _bearer_from_auth_header(authorization)
    if token:
        payload = safe_decode_token(token)
        if payload and payload.get("type") == "access" and payload.get("sub"):
            user = db.get(User, int(payload["sub"]))
            if user and user.is_active:
                return user

    # Dev fallback
    if not settings.is_dev:
        # In prod, require auth (but we keep the signature stable)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    user = db.execute(select(User).where(User.username == "demo")).scalar_one_or_none()
    if user:
        return user
    user = User(username="demo", password_hash=hash_password("demo"), is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

