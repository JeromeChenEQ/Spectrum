"""SQLAlchemy engine/session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_database_url, settings

DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"sslmode": settings.db_sslmode},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
