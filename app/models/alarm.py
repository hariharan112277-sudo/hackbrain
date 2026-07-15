"""
Alarm Model — Frozen PostgreSQL schema contract mapping (table: alarms)
Track A (Database Layer) — Stage 1
"""

from sqlalchemy import Column, String, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Alarm(Base):
    __tablename__ = 'alarms'

    alarm_id = Column(String(30), primary_key=True)
    asset_id = Column(String(20), ForeignKey('assets.asset_id'))
    severity = Column(String(20))  # critical, warning, resolved
    code = Column(String(40))
    message = Column(String)
    value = Column(Numeric)
    threshold = Column(Numeric)
    ts = Column(DateTime(timezone=True), nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))

    asset = relationship("Asset", back_populates="alarms")
