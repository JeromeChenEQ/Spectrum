"""Environment configuration for the FastAPI service."""

from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    app_env: str = os.getenv("APP_ENV", "development")
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "spectrum_senioraid")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    max_audio_seconds: int = int(os.getenv("MAX_AUDIO_SECONDS", "60"))


settings = Settings()