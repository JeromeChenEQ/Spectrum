"""SQLAlchemy engine/session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

if settings.app_env == "development":
    # Local MySQL for development/testing
    DATABASE_URL = (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
    )
    _connect_args: dict = {}
else:
    # Supabase Postgres for production
    DATABASE_URL = settings.supabase_db_url
    _connect_args = {"sslmode": "require"}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)