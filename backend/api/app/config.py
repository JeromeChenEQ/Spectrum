"""Environment configuration for the FastAPI service."""

from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _int_env(key: str, default: str) -> int:
    """Safely parse an integer env var."""
    try:
        return int(os.getenv(key, default))
    except ValueError:
        return int(default)


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    app_env: str = os.getenv("APP_ENV", "development")

    # MySQL (local development)
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = _int_env("MYSQL_PORT", "3306")
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "spectrum_senioraid")

    # Supabase Postgres (production)
    supabase_db_url: str = os.getenv("SUPABASE_DB_URL", "")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    max_audio_seconds: int = _int_env("MAX_AUDIO_SECONDS", "60")


settings = Settings()

if settings.app_env != "development" and not settings.supabase_db_url:
    raise RuntimeError("SUPABASE_DB_URL must be set for non-development environments")