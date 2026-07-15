"""
Asset Domain Models — Frozen PostgreSQL schema contract mappings
Track A (Database Layer) — Stage 1

Tables: assets, sensors, telemetry, events, maintenance_logs
"""

from sqlalchemy import Column, String, Date, DateTime, BigInteger, Numeric, ForeignKey, text
from sqlalchemy.orm import relationship
from app.database import Base

class Asset(Base):
    __tablename__ = 'assets'

    asset_id = Column(String(20), primary_key=True)
    name = Column(String(120), nullable=False)
    plant_id = Column(String(20), nullable=False)
    line_id = Column(String(20), nullable=False)
    machine_id = Column(String(20), nullable=False, unique=True)
    asset_type = Column(String(60))
    install_date = Column(Date)
    criticality = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))

    # Relationships
    sensors = relationship("Sensor", back_populates="asset")
    telemetries = relationship("Telemetry", back_populates="asset")
    events = relationship("Event", back_populates="asset")
    alarms = relationship("Alarm", back_populates="asset")
    maintenance_logs = relationship("MaintenanceLog", back_populates="asset")


class Sensor(Base):
    __tablename__ = 'sensors'

    sensor_id = Column(String(20), primary_key=True)
    asset_id = Column(String(20), ForeignKey('assets.asset_id'))
    metric_name = Column(String(60), nullable=False)
    unit = Column(String(20))
    min_range = Column(Numeric)
    max_range = Column(Numeric)

    asset = relationship("Asset", back_populates="sensors")


class Telemetry(Base):
    __tablename__ = 'telemetry'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_id = Column(String(20), ForeignKey('assets.asset_id'))
    ts = Column(DateTime(timezone=True), nullable=False)
    temperature_c = Column(Numeric)
    pressure_bar = Column(Numeric)
    vibration_mm_s = Column(Numeric)
    rpm = Column(Numeric)
    voltage_v = Column(Numeric)
    current_a = Column(Numeric)
    energy_kwh = Column(Numeric)
    status = Column(String(20))

    asset = relationship("Asset", back_populates="telemetries")


class Event(Base):
    __tablename__ = 'events'

    event_id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_id = Column(String(20), ForeignKey('assets.asset_id'))
    ts = Column(DateTime(timezone=True), nullable=False)
    event_type = Column(String(40))
    description = Column(String)

    asset = relationship("Asset", back_populates="events")


class MaintenanceLog(Base):
    __tablename__ = 'maintenance_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_id = Column(String(20), ForeignKey('assets.asset_id'))
    performed_at = Column(DateTime(timezone=True))
    description = Column(String)
    technician = Column(String(80))

    asset = relationship("Asset", back_populates="maintenance_logs")
