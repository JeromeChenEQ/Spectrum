"""Alert endpoints for device ingestion and helpdesk operations."""

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Alert, Box
from app.schemas import AcknowledgeResponse, AlertResponse
from app.services.openai_audio_service import analyze_audio_single_call
from app.services.realtime_broadcaster import alert_connection_manager

alerts_router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])



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

    if not audio_file.filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only WAV uploads are accepted")

    audio_bytes = await audio_file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="audio_file is empty")

    ai_result = analyze_audio_single_call(audio_bytes, audio_file.content_type or "audio/wav")
    severity = str(ai_result.get("severity", "ROUTINE")).upper()
    if severity not in {"EMERGENCY", "URGENT", "ROUTINE"}:
        severity = "ROUTINE"

    alert = Alert(
        box_id=box_id,
        detected_language=ai_result.get("detected_language", "Unknown"),
        transcript=ai_result.get("transcript", ""),
        english_translation=ai_result.get("english_translation", ""),
        severity=severity,
        status="open",
        is_simulated_ai=bool(ai_result.get("is_simulated_ai", False)),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    payload = AlertResponse.model_validate(alert).model_dump(mode="json")
    await alert_connection_manager.broadcast({"type": "alert_created", "payload": payload})
    return alert


@alerts_router.get("", response_model=list[AlertResponse])
def list_alerts(db: Session = Depends(get_db_session)):
    """List all alerts ordered by newest first."""
    try:
        alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
        return alerts
    except SQLAlchemyError as error:
        raise HTTPException(status_code=500, detail=f"Database query failed: {error}") from error


@alerts_router.patch("/{alert_id}/acknowledge", response_model=AcknowledgeResponse)
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db_session)):
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
    await alert_connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_connection_manager.disconnect(websocket)
