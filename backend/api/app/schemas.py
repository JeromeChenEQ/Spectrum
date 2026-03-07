"""Pydantic schemas for API responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    """Serialized alert payload for API and websocket clients."""

    model_config = ConfigDict(from_attributes=True)

    alert_id: int
    box_id: int
    detected_language: str
    transcript: str
    english_translation: str
    severity: Literal["URGENT", "UNCERTAIN", "NON-URGENT"]
    confidence_score: float
    keywords: str
    distress_indicators: str
    status: Literal["open", "acknowledged"]

    created_at: datetime
    acknowledged_at: datetime | None = None


class AcknowledgeResponse(BaseModel):
    """Response payload for acknowledge action."""

    alert_id: int
    status: str