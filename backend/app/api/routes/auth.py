from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginIn, RefreshIn, TokenPair, UserOut
from app.security.jwt import create_token, safe_decode_token
from app.security.passwords import verify_password
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/login", response_model=TokenPair)
def login(data: LoginIn, db: Session = Depends(get_db)) -> TokenPair:
    user = db.execute(select(User).where(User.username == data.username)).scalar_one_or_none()
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = create_token(
        subject=str(user.id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_MINUTES),
    )
    refresh = create_token(
        subject=str(user.id),
        token_type="refresh",
        expires_delta=timedelta(days=settings.JWT_REFRESH_DAYS),
    )
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshIn, db: Session = Depends(get_db)) -> TokenPair:
    payload = safe_decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access = create_token(
        subject=str(user.id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_MINUTES),
    )
    refresh = create_token(
        subject=str(user.id),
        token_type="refresh",
        expires_delta=timedelta(days=settings.JWT_REFRESH_DAYS),
    )
    return TokenPair(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
