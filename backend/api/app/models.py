"""SQLAlchemy ORM models."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
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
    box_id = Column(Integer, ForeignKey("boxes.box_id"), nullable=False, index=True)
    detected_language = Column(String(40), nullable=False)
    transcript = Column(Text, nullable=False)
    english_translation = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.0)
    keywords = Column(Text, nullable=True)
    distress_indicators = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)

    box = relationship("Box", back_populates="alerts")
