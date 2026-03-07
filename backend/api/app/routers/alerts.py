"""Alert endpoints for device ingestion and helpdesk operations."""

import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Alert, Box, User
from app.schemas import AcknowledgeResponse, AlertResponse
from app.services.auth_service import get_current_active_user, get_current_active_user_from_token
from app.services.openai_audio_service import analyze_audio_single_call
from app.services.realtime_broadcaster import alert_connection_manager

alerts_router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])

# ~16 kHz, 16-bit mono WAV estimate per second + generous overhead
MAX_UPLOAD_BYTES = settings.max_audio_seconds * 16_000 * 2 + 44



def get_db_session():
    """Yield database session for request scope."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@alerts_router.post("/from-device", response_model=AlertResponse, status_code=201)
async def create_alert_from_device(
    box_id: int = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
):
    """Create alert from uploaded device audio file."""
    box = db.query(Box).filter(Box.box_id == box_id).first()
    if box is None:
        raise HTTPException(status_code=404, detail="box_id not found")

    audio_bytes = await audio_file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="audio_file is empty")
    if len(audio_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Audio file exceeds maximum allowed size")

    try:
        ai_result = await asyncio.to_thread(
            analyze_audio_single_call, audio_bytes, audio_file.content_type or "audio/wav"
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    severity = str(ai_result.get("severity", "UNCERTAIN")).upper()
    if severity not in {"URGENT", "UNCERTAIN", "NON-URGENT"}:
        severity = "UNCERTAIN"

    alert = Alert(
        box_id=box_id,
        detected_language=ai_result.get("detected_language", "Unknown"),
        transcript=ai_result.get("transcript", ""),
        english_translation=ai_result.get("english_translation", ""),
        severity=severity,
        status="open",
        confidence_score=ai_result.get("confidence_score", 0.0),
        keywords=ai_result.get("keywords", ""),
        distress_indicators=ai_result.get("distress_indicators", "")
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    payload = AlertResponse.model_validate(alert).model_dump(mode="json")
    await alert_connection_manager.broadcast({"type": "alert_created", "payload": payload})
    return alert


@alerts_router.get("", response_model=list[AlertResponse])
def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
):
    """List all alerts ordered by newest first."""
    try:
        alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
        return alerts
    except SQLAlchemyError as error:
        raise HTTPException(status_code=500, detail=f"Database query failed: {error}") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {error}") from error


@alerts_router.patch("/{alert_id}/acknowledge", response_model=AcknowledgeResponse)
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
):
    """Acknowledge an existing alert."""
    try:
        alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if alert is None:
            raise HTTPException(status_code=404, detail="alert not found")

        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        db.commit()
    except SQLAlchemyError as error:
        raise HTTPException(status_code=500, detail=f"Database update failed: {error}") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {error}") from error

    await alert_connection_manager.broadcast(
        {
            "type": "alert_acknowledged",
            "payload": {"alert_id": alert_id, "status": "acknowledged"},
        }
    )
    return AcknowledgeResponse(alert_id=alert_id, status="acknowledged")


@alerts_router.websocket_route("/ws")
async def alerts_websocket(websocket: WebSocket):
    """WebSocket channel for realtime alert events."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    db = SessionLocal()
    try:
        get_current_active_user_from_token(token, db)
    except HTTPException:
        await websocket.close(code=4401)
        return
    finally:
        db.close()

    await alert_connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_connection_manager.disconnect(websocket)
