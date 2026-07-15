"""
ORM Models Package — Declarative Schema Mappings
Track A (Database Layer) — Stage 1

Imports every declarative model so that:

1. All tables are registered on ``Base.metadata`` (required for DDL
   compilation, Alembic autogenerate, and ``Base.metadata.create_all``).
2. All ``relationship()`` string references (e.g. ``relationship("Sensor")``)
   resolve regardless of consumer import order — preventing circular-import
   and unresolved-mapper traps.

Consumers should import from this package::

    from app.models import User, Asset, Sensor, Telemetry, Event, Alarm, MaintenanceLog

Pydantic API schemas for these tables live in ``app.models.schemas``.
"""

from app.database import Base
from app.models.user import User
from app.models.asset import Asset, Sensor, Telemetry, Event, MaintenanceLog
from app.models.alarm import Alarm

__all__ = [
    "Base",
    "User",
    "Asset",
    "Sensor",
    "Telemetry",
    "Event",
    "MaintenanceLog",
    "Alarm",
]
