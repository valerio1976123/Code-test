from __future__ import annotations

from cryptography.fernet import Fernet

from app.core.config import settings


def _fernet() -> Fernet:
    # settings.APP_SECRET_KEY must be a valid Fernet key (urlsafe base64)
    return Fernet(settings.APP_SECRET_KEY.encode("utf-8"))


def encrypt_secret(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    token = _fernet().encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_secret(token: str | None) -> str | None:
    if token is None or token == "":
        return None
    value = _fernet().decrypt(token.encode("utf-8"))
    return value.decode("utf-8")
