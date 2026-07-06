"""
SQLAlchemy Declarative Model schemas mapping operational physical assets,
gateways, runtime machines, metrics sensors, and telemetry tracking arrays.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, ForeignKey,
    Text, Enum, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.compiler import compiles

# Enable clean SQLite testing support without altering PostgreSQL production DDL
@compiles(UUID, 'sqlite')
def compile_uuid_sqlite(type_, compiler, **kw):
    return 'CHAR(36)'


@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return 'JSON'


Base = declarative_base()


class OperationalStatus(str, PyEnum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


class AlarmSeverity(str, PyEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlarmState(str, PyEnum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CLEARED = "CLEARED"


class Plant(Base):
    __tablename__ = "plants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    location = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    lines = relationship("ProductionLine", back_populates="plant", cascade="all, delete-orphan")


class ProductionLine(Base):
    __tablename__ = "production_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plant_id = Column(UUID(as_uuid=True), ForeignKey("plants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    plant = relationship("Plant", back_populates="lines")
    assets = relationship("Asset", back_populates="production_line")

    __table_args__ = (UniqueConstraint('plant_id', 'name', name='uq_plant_line_name'),)


class Gateway(Base):
    __tablename__ = "gateways"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=False)
    mac_address = Column(String(17), nullable=False, unique=True)
    firmware_version = Column(String(50), nullable=False)
    protocol = Column(String(20), default="MQTT", nullable=False)  # OPC-UA, MQTT, Modbus
    status = Column(Enum(OperationalStatus), default=OperationalStatus.ONLINE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    machines = relationship("Machine", back_populates="gateway")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_line_id = Column(UUID(as_uuid=True), ForeignKey("production_lines.id"), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # Rotating, Thermal, Electrical
    manufacturer = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    criticality = Column(String(20), nullable=False)  # Low, Medium, High, Mission-Critical
    installation_date = Column(DateTime, nullable=False)
    commission_date = Column(DateTime, nullable=True)
    status = Column(Enum(OperationalStatus), default=OperationalStatus.ONLINE, nullable=False)
    metadata_fields = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    production_line = relationship("ProductionLine", back_populates="assets")
    machine = relationship("Machine", uselist=False, back_populates="asset")


class Machine(Base):
    __tablename__ = "machines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), unique=True, nullable=False)
    gateway_id = Column(UUID(as_uuid=True), ForeignKey("gateways.id"), nullable=False)
    firmware_version = Column(String(50), nullable=False)
    operating_hours = Column(Float, default=0.0, nullable=False)
    runtime_counter = Column(Float, default=0.0, nullable=False)
    current_mode = Column(String(30), default="AUTOMATIC", nullable=False)  # MANUAL, AUTOMATIC, JOG
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    asset = relationship("Asset", back_populates="machine")
    gateway = relationship("Gateway", back_populates="machines")
    sensors = relationship("Sensor", back_populates="machine", cascade="all, delete-orphan")
    telemetry_records = relationship("Telemetry", back_populates="machine")
    events = relationship("MachineEvent", back_populates="machine")
    alarms = relationship("Alarm", back_populates="machine")
    maintenance_records = relationship("MaintenanceLog", back_populates="machine")

    __table_args__ = (CheckConstraint('operating_hours >= 0', name='chk_operating_hours_positive'),)


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    sensor_type = Column(String(50), nullable=False)  # Vibration, Temp, Flow
    measurement_unit = Column(String(20), nullable=False)  # mm/s, Celsius, m3/h
    sampling_rate_hz = Column(Float, nullable=False)
    calibration_offset = Column(Float, default=0.0, nullable=False)
    lower_threshold = Column(Float, nullable=True)
    upper_threshold = Column(Float, nullable=True)
    status = Column(Enum(OperationalStatus), default=OperationalStatus.ONLINE, nullable=False)
    metadata_fields = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    machine = relationship("Machine", back_populates="sensors")
    telemetry_records = relationship("Telemetry", back_populates="sensor")
    alarms = relationship("Alarm", back_populates="sensor")

    __table_args__ = (UniqueConstraint('machine_id', 'name', name='uq_machine_sensor_name'),)


class Telemetry(Base):
    """High-frequency industrial timeseries component storage core."""
    __tablename__ = "telemetry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False, index=True)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=False, index=True)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("sensors.id"), nullable=False, index=True)
    measured_value = Column(Float, nullable=False)
    quality_code = Column(Integer, default=192, nullable=False)  # OPC-DA standard code (192 = Good Quality)
    alarm_status = Column(String(20), default="NORMAL", nullable=False)  # NORMAL, LO, HI, LOLO, HIHI
    sequence_number = Column(Integer, nullable=False)
    metadata_fields = Column(JSONB, default=dict, nullable=False)

    machine = relationship("Machine", back_populates="telemetry_records")
    sensor = relationship("Sensor", back_populates="telemetry_records")

    __table_args__ = (
        Index('idx_telemetry_machine_timestamp', 'machine_id', 'timestamp'),
        Index('idx_telemetry_sensor_timestamp', 'sensor_id', 'timestamp'),
    )


class Alarm(Base):
    __tablename__ = "alarms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=False)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("sensors.id"), nullable=False)
    severity = Column(Enum(AlarmSeverity), nullable=False)
    state = Column(Enum(AlarmState), default=AlarmState.ACTIVE, nullable=False)
    trigger_timestamp = Column(DateTime, nullable=False)
    ack_timestamp = Column(DateTime, nullable=True)
    clear_timestamp = Column(DateTime, nullable=True)
    trigger_value = Column(Float, nullable=False)
    threshold_violated = Column(String(50), nullable=False)
    operator_notes = Column(Text, nullable=True)

    machine = relationship("Machine", back_populates="alarms")
    sensor = relationship("Sensor", back_populates="alarms")


class MachineEvent(Base):
    __tablename__ = "machine_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)  # STARTUP, SHUTDOWN, EMERGENCY_STOP
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    payload = Column(JSONB, default=dict, nullable=False)  # Snapshot variables state
    operator_id = Column(UUID(as_uuid=True), nullable=True)

    machine = relationship("Machine", back_populates="events")


class Operator(Base):
    __tablename__ = "operators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    badge_number = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    assigned_shift = Column(String(20), nullable=False)  # DAY, NIGHT, SWING
    is_active = Column(Boolean, default=True, nullable=False)


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=False)
    technician_id = Column(UUID(as_uuid=True), ForeignKey("operators.id"), nullable=False)
    maintenance_type = Column(String(30), nullable=False)  # PREVENTIVE, CORRECTIVE, PREDICTIVE
    scheduled_time = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    parts_replaced = Column(JSONB, default=list, nullable=False)  # Structured manifest array
    operational_notes = Column(Text, nullable=True)
    status = Column(String(20), default="SCHEDULED", nullable=False)  # COMPLETED, IN_PROGRESS

    machine = relationship("Machine", back_populates="maintenance_records")
