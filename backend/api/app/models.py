"""SQLAlchemy ORM models."""

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Box(Base):
    """Represents a deployed senior device box."""

    __tablename__ = "boxes"

    box_id = Column(Integer, primary_key=True, index=True)
    resident_name = Column(String(120), nullable=False)
    address = Column(String(255), nullable=False)
    contact_number = Column(String(30), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    alerts = relationship("Alert", back_populates="box")


class Alert(Base):
    """Represents one emergency button press event."""

    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, index=True)
    box_id = Column(Integer, ForeignKey("boxes.box_id"), nullable=False)
    detected_language = Column(String(40), nullable=False)
    transcript = Column(Text, nullable=False)
    english_translation = Column(Text, nullable=False)
    severity = Column(Enum("EMERGENCY", "URGENT", "ROUTINE", name="severity_enum"), nullable=False)
    status = Column(Enum("open", "acknowledged", name="alert_status_enum"), nullable=False, default="open")
    is_simulated_ai = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)

    box = relationship("Box", back_populates="alerts")