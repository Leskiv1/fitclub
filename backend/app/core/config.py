"""Application settings loaded from environment variables and the root .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    app_name: str = "FitClub API"
    database_url: str
    test_database_url: str | None = None
    cors_origins: list[str] = ["http://localhost:5173"]
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(480, gt=0)
    club_timezone: str = "Europe/Kyiv"

    # daily check of expiring memberships; switched off in tests
    scheduler_enabled: bool = True

    # e-mail: without SMTP_HOST letters go to the log (imitation)
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "FitClub <noreply@fitclub.example>"


@lru_cache
def get_settings() -> Settings:
    return Settings()
