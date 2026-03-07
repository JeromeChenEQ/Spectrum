"""FastAPI application bootstrap."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import Base
from app.database import engine
from app.routers.alerts import alerts_router
from app.routers.auth import auth_router

if settings.auto_create_tables:
    Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables automatically in development only."""
    if settings.app_env == "development":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Spectrum SeniorAid API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Service health endpoint."""
    return {"status": "ok"}


app.include_router(alerts_router)
app.include_router(auth_router)
