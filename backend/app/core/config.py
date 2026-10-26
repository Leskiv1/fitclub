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


@lru_cache
def get_settings() -> Settings:
    return Settings()
