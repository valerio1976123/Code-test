from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[3]

APP_MODES = {"dev", "prod"}


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

    # dev|prod toggle. In dev we use mock market data providers.
    APP_MODE: str = Field("dev", description="Application mode: dev|prod")

    # Preferred DB URL. If not set, SQLITE_PATH is used.
    # Examples:
    # - sqlite:////abs/path/app.db
    # - postgresql+psycopg://user:pass@host:5432/dbname
    DATABASE_URL: str | None = Field(default=None, description="SQLAlchemy database URL (optional)")

    SQLITE_PATH: str = "./data/crazynet_backups.db"
    BACKUP_ROOT: str = "./backups"
    MAX_PARALLEL_BACKUPS: int = 3

    # Market monitor refresh cadence (seconds). Kept conservative for dev.
    MARKET_PRICE_REFRESH_SECONDS: int = 300
    MARKET_MACRO_REFRESH_SECONDS: int = 3600
    MARKET_PREDICTION_REFRESH_SECONDS: int = 900

    # Placeholder API keys for future real providers (unused in dev mock mode).
    API_KEY_ALPHA_VANTAGE: str | None = None
    API_KEY_YAHOO_FINANCE: str | None = None

    @property
    def sqlite_url(self) -> str:
        p = Path(self.SQLITE_PATH)
        if not p.is_absolute():
            p = BACKEND_DIR / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{p.as_posix()}"

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return self.sqlite_url

    @property
    def is_dev(self) -> bool:
        return self.APP_MODE.lower().strip() == "dev"

    @property
    def is_prod(self) -> bool:
        return self.APP_MODE.lower().strip() == "prod"

    def validate(self) -> None:
        mode = self.APP_MODE.lower().strip()
        if mode not in APP_MODES:
            raise ValueError(f"Invalid APP_MODE={self.APP_MODE!r}. Expected one of: {sorted(APP_MODES)}")

    @property
    def backup_root_path(self) -> Path:
        p = Path(self.BACKUP_ROOT)
        if not p.is_absolute():
            p = BACKEND_DIR / p
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
settings.validate()
