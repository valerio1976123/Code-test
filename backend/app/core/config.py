from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_DIR / ".env"), env_file_encoding="utf-8", extra="ignore")

    # Defaults are provided so unit tests can run without a .env.
    # For production, always override via backend/.env.
    APP_SECRET_KEY: str = Field(
        "8q2JcV3Vw8h6iR3e7iVx6A2oHkQmHcVqVgVYzJ9pR4c=",
        description="Fernet key (urlsafe base64)",
    )
    JWT_SECRET: str = Field("dev-jwt-secret-change-me", description="JWT signing secret")

    JWT_ACCESS_MINUTES: int = 15
    JWT_REFRESH_DAYS: int = 14

    SQLITE_PATH: str = "./data/crazynet_backups.db"
    BACKUP_ROOT: str = "./backups"
    MAX_PARALLEL_BACKUPS: int = 3

    @property
    def sqlite_url(self) -> str:
        p = Path(self.SQLITE_PATH)
        if not p.is_absolute():
            p = BACKEND_DIR / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{p.as_posix()}"

    @property
    def backup_root_path(self) -> Path:
        p = Path(self.BACKUP_ROOT)
        if not p.is_absolute():
            p = BACKEND_DIR / p
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
