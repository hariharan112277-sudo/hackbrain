"""
In-Memory Repository Stubs.

Lightweight, deterministic stand-in implementations of the Member 2 repository
contracts. They are useful for:
- Local development without a running database
- Fast unit tests
- Demonstrating the Phase 4 API surface before Member 2 wiring is complete

In production these are replaced by concrete adapters wired to the industrial
database (see app.repositories.adapters).
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.repositories.interfaces import (
    IMachineRepository,
    ITelemetryRepository,
    IAlarmRepository,
    IMetadataRepository,
)


class InMemoryMachineRepository(IMachineRepository):
    """Volatile machine registry backed by a Python list."""

    def __init__(self, seed: Optional[List[Dict[str, Any]]] = None):
        self._store: List[Dict[str, Any]] = list(seed) if seed else []

    async def get_by_id(self, machine_id: str) -> Optional[Dict[str, Any]]:
        for machine in self._store:
            if str(machine.get("id")) == str(machine_id):
                return machine
        return None

    async def list_machines(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        return self._store[skip : skip + limit]


class InMemoryTelemetryRepository(ITelemetryRepository):
    """Volatile telemetry store keyed by machine_id."""

    def __init__(self, seed: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        self._store: Dict[str, List[Dict[str, Any]]] = dict(seed) if seed else {}

    async def get_latest_telemetry(self, machine_id: str) -> Optional[Dict[str, Any]]:
        points = self._store.get(str(machine_id), [])
        if not points:
            return None
        latest = points[-1]
        return {
            "machine_id": str(machine_id),
            "timestamp": latest.get("timestamp") or datetime.now(timezone.utc),
            "metrics": latest.get("metrics", {}),
        }

    async def get_historical_telemetry(
        self, machine_id: str, metric: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        points = self._store.get(str(machine_id), [])
        filtered = [
            {
                "timestamp": p.get("timestamp"),
                "value": p.get("metrics", {}).get(metric),
            }
            for p in points
            if metric in p.get("metrics", {})
        ]
        return filtered[-limit:]


class InMemoryAlarmRepository(IAlarmRepository):
    """Volatile alarm registry with severity filtering and resolution."""

    def __init__(self, seed: Optional[List[Dict[str, Any]]] = None):
        self._store: List[Dict[str, Any]] = list(seed) if seed else []

    async def get_active_alarms(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        active = [a for a in self._store if a.get("is_active", True)]
        if severity:
            active = [a for a in active if a.get("severity") == severity]
        return active

    async def resolve_alarm(self, alarm_id: str, resolved_by: str) -> bool:
        for alarm in self._store:
            if str(alarm.get("id")) == str(alarm_id):
                alarm["is_active"] = False
                alarm["resolved_by"] = resolved_by
                alarm["resolved_at"] = datetime.now(timezone.utc).isoformat()
                return True
        return False


class InMemoryMetadataRepository(IMetadataRepository):
    """Volatile metadata provider with engineering-unit enrichment."""

    def __init__(self, seed: Optional[Dict[str, Dict[str, Any]]] = None):
        self._store: Dict[str, Dict[str, Any]] = dict(seed) if seed else {}

    async def get_machine_metadata(self, machine_id: str) -> Dict[str, Any]:
        base = self._store.get(str(machine_id), {"machine_id": str(machine_id)})
        return {
            **base,
            "engineering_units": {
                "temperature": "CELSIUS",
                "pressure": "BAR",
                "vibration": "MM/S",
                "speed": "RPM",
            },
            "version": "v4.0",
        }


def build_default_stubs() -> Dict[str, Any]:
    """Factory that returns a complete set of seeded in-memory repositories."""
    now = datetime.now(timezone.utc)
    machine_id = str(uuid4())
    alarm_id = str(uuid4())

    machines = [
        {
            "id": machine_id,
            "name": "Demo CNC Lathe",
            "type": "CNC",
            "status": "online",
            "location": "Line-A",
        }
    ]

    telemetry = {
        machine_id: [
            {
                "timestamp": now,
                "metrics": {"vibration": 2.1, "temperature": 65.4},
            },
            {
                "timestamp": now,
                "metrics": {"vibration": 2.3, "temperature": 66.1},
            },
        ]
    }

    alarms = [
        {
            "id": alarm_id,
            "machine_id": machine_id,
            "severity": "medium",
            "message": "Temperature threshold exceeded",
            "timestamp": now,
            "is_active": True,
        }
    ]

    metadata = {
        machine_id: {
            "machine_id": machine_id,
            "asset": {"name": "Demo CNC Lathe", "criticality": "High"},
            "sensor_count": 4,
        }
    }

    return {
        "machine": InMemoryMachineRepository(machines),
        "telemetry": InMemoryTelemetryRepository(telemetry),
        "alarm": InMemoryAlarmRepository(alarms),
        "metadata": InMemoryMetadataRepository(metadata),
    }
