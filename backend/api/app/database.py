"""SQLAlchemy engine/session factory."""

import ssl

import certifi
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_database_url, settings

DATABASE_URL = get_database_url()

connect_args = {}
if settings.db_sslmode == "require":
    if settings.db_ssl_verify:
        ca_file = settings.db_ssl_ca_file or certifi.where()
        connect_args["ssl_context"] = ssl.create_default_context(cafile=ca_file)
    else:
        connect_args["ssl_context"] = ssl._create_unverified_context()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
