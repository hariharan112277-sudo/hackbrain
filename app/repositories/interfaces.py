"""
Repository Layer Interfaces (Member 2 Contracts).

To interact with the database tier owned by Member 2 without modifying or
writing direct database engines, we define clean abstract interfaces that our
service layer consumes.

These contracts enforce Clean Architecture boundaries: Member 1 (REST API /
business services) depends ONLY on these abstractions. Concrete implementations
are supplied by Member 2's repository / integration layer and injected at
runtime via FastAPI dependencies.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IMachineRepository(ABC):
    @abstractmethod
    async def get_by_id(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Return a single machine record by its identifier."""
        pass

    @abstractmethod
    async def list_machines(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Return a paginated list of machine registry records."""
        pass


class ITelemetryRepository(ABC):
    @abstractmethod
    async def get_latest_telemetry(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Return the most recent telemetry snapshot for a machine."""
        pass

    @abstractmethod
    async def get_historical_telemetry(
        self, machine_id: str, metric: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Return historical telemetry points for a machine and metric."""
        pass


class IAlarmRepository(ABC):
    @abstractmethod
    async def get_active_alarms(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return active (non-cleared) alarms, optionally filtered by severity."""
        pass

    @abstractmethod
    async def resolve_alarm(self, alarm_id: str, resolved_by: str) -> bool:
        """Acknowledge / clear an alarm. Returns True if the alarm existed."""
        pass


class IMetadataRepository(ABC):
    @abstractmethod
    async def get_machine_metadata(self, machine_id: str) -> Dict[str, Any]:
        """Return enriched metadata for a machine (asset, sensors, engineering units)."""
        pass
