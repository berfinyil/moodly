"""Central application configuration loaded from environment variables (.env)."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# backend/ directory — resolved relative to this file so it works from any CWD
BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

INSECURE_SECRET_KEY = "change-me"


class Settings(BaseSettings):
    """Application settings.

    Values are read from environment variables or the backend/.env file.
    SQLite is used for local development; switching to PostgreSQL in
    production only requires changing DATABASE_URL.
    """

    app_name: str = "Moodly"
    environment: str = "development"

    database_url: str = "sqlite:///./moodly.db"

    secret_key: str = INSECURE_SECRET_KEY
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    ai_api_key: str = ""

    # Comma-separated, e.g. CORS_ORIGINS=https://app.example.com,https://www.app.example.com
    # NoDecode turns off pydantic's automatic JSON parsing for this field —
    # without it, a plain comma-separated env var crashes at startup.
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        """Allow a comma-separated string so hosting panels can set it."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def resolved_database_url(self) -> str:
        """Normalize the database URL for SQLAlchemy.

        - Relative SQLite paths are anchored to the backend directory, so the
          same file is used no matter where the server is started from.
        - `postgres://` (handed out by Render, Railway, Heroku) is rewritten to
          `postgresql://`, which is what SQLAlchemy 2.x expects.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)

        sqlite_prefix = "sqlite:///./"
        if url.startswith(sqlite_prefix):
            db_file = BACKEND_DIR / url.removeprefix(sqlite_prefix)
            return f"sqlite:///{db_file}"
        return url


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
