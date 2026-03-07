"""Environment configuration for the FastAPI service."""

from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse
from dotenv import load_dotenv

APP_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(APP_ROOT / ".env")


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
    supabase_db_url: str = (
        os.getenv("SUPABASE_DB_URL")
        or os.getenv("DB_URL")
        or os.getenv("DATABASE_URL")
        or ""
    )
    supabase_db_password: str = (
        os.getenv("SUPABASE_DB_PASSWORD")
        or os.getenv("DB_PASSWORD")
        or ""
    )
    db_sslmode: str = os.getenv("DB_SSLMODE", "require")
    db_ssl_ca_file: str = os.getenv("DB_SSL_CA_FILE", "")
    db_ssl_verify: bool = os.getenv("DB_SSL_VERIFY", "true").lower() == "true"
    auto_create_tables: bool = os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    max_audio_seconds: int = _int_env("MAX_AUDIO_SECONDS", "60")

settings = Settings()


def get_database_url() -> str:
    """Build the SQLAlchemy URL for Supabase PostgreSQL."""
    if not settings.supabase_db_url:
        raise ValueError("SUPABASE_DB_URL (or DB_URL / DATABASE_URL) is required")

    database_url = settings.supabase_db_url
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    if settings.supabase_db_password:
        encoded_password = quote_plus(settings.supabase_db_password)
        database_url = (
            database_url
            .replace("[YOUR-PASSWORD]", encoded_password)
            .replace("<YOUR-PASSWORD>", encoded_password)
            .replace("YOUR_PASSWORD", encoded_password)
        )

    if "[YOUR-PASSWORD]" in database_url or "<YOUR-PASSWORD>" in database_url:
        raise ValueError(
            "SUPABASE_DB_PASSWORD is required when SUPABASE_DB_URL contains a password placeholder"
        )

    parsed = urlparse(database_url)
    if parsed.scheme == "postgresql":
        database_url = urlunparse(parsed._replace(scheme="postgresql+pg8000"))
        parsed = urlparse(database_url)

    if parsed.hostname and parsed.hostname.endswith(".pooler.supabase.com") and parsed.port == 5432:
        netloc = parsed.netloc.rsplit(":5432", 1)[0] + ":6543"
        database_url = urlunparse(parsed._replace(netloc=netloc))
        parsed = urlparse(database_url)

    # pg8000 uses ssl_context from SQLAlchemy connect_args, so strip sslmode URL param.
    if parsed.scheme == "postgresql+pg8000" and parsed.query:
        query_pairs = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k != "sslmode"]
        database_url = urlunparse(parsed._replace(query=urlencode(query_pairs)))

    return database_url
