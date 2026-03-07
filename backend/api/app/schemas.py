"""Pydantic schemas for API responses."""

from datetime import datetime
from pydantic import BaseModel


class AlertResponse(BaseModel):
    """Serialized alert payload for API and websocket clients."""

    alert_id: int
    box_id: int
    detected_language: str
    transcript: str
    english_translation: str
    severity: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AcknowledgeResponse(BaseModel):
    """Response payload for acknowledge action."""

    alert_id: int
    status: str