"""
Industrial Operating Brain (IOB): Phase 5 — Industrial Database Layer Architecture.
"""

from .config import DatabaseSettings, db_settings, load_config_from_yaml
from .exceptions import (
    IOBDatabaseError,
    ConnectionError,
    OperationalTimeoutError,
    ConstraintViolationError,
    RecordNotFoundError,
    BulkOperationError
)
from .logger import get_industrial_logger
from .connection import DatabaseConnectionManager, connection_manager, get_db_context
from .interfaces import IBaseCRUD, IRepository
from .models import (
    Base,
    OperationalStatus,
    AlarmSeverity,
    AlarmState,
    Plant,
    ProductionLine,
    Gateway,
    Asset,
    Machine,
    Sensor,
    Telemetry,
    Alarm,
    MachineEvent,
    Operator,
    MaintenanceLog
)
from .crud import BaseCRUD
from .repository import (
    AssetRepository,
    MachineRepository,
    SensorRepository,
    TelemetryRepository,
    EventRepository,
    AlarmRepository,
    MaintenanceRepository
)

__version__ = "5.0.0-DB"
__all__ = [
    "DatabaseSettings", "db_settings", "load_config_from_yaml",
    "IOBDatabaseError", "ConnectionError", "OperationalTimeoutError",
    "ConstraintViolationError", "RecordNotFoundError", "BulkOperationError",
    "get_industrial_logger", "DatabaseConnectionManager", "connection_manager", "get_db_context",
    "IBaseCRUD", "IRepository", "Base", "OperationalStatus", "AlarmSeverity", "AlarmState",
    "Plant", "ProductionLine", "Gateway", "Asset", "Machine", "Sensor", "Telemetry",
    "Alarm", "MachineEvent", "Operator", "MaintenanceLog",
    "BaseCRUD", "AssetRepository", "MachineRepository", "SensorRepository",
    "TelemetryRepository", "EventRepository", "AlarmRepository", "MaintenanceRepository"
]
