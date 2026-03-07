"""FastAPI application bootstrap."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import Base
from app.database import engine
from app.routers.alerts import alerts_router

if settings.auto_create_tables:
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="Spectrum SeniorAid API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Service health endpoint."""
    return {"status": "ok"}


app.include_router(alerts_router)
