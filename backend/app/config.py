"""
Application configuration using pydantic-settings.
Reads from environment variables and .env file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings

import os

BASE_DIR = Path(__file__).resolve().parent.parent

# On Render, use /tmp for SQLite (ephemeral filesystem)
_db_dir = Path("/tmp") if os.environ.get("RENDER") else BASE_DIR
_db_path = _db_dir / "eigenknot.db"


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    APP_NAME: str = "eigen knot API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{_db_path}"

    # CORS — open for now; lock down to specific Ghost domain in production
    CORS_ORIGINS: list[str] = ["*"]

    # Payment webhook secret (placeholder for PortOne/Toss)
    PAYMENT_WEBHOOK_SECRET: str = ""

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
