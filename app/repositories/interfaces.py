"""
Repository Interfaces for Member 2 Integration
Phase 5: Abstract contracts defining the data access layer boundaries.

These interfaces are implemented by Member 2's repository layer.
Member 1 consumes these interfaces without modifying DB engines, 
schema migrations, or MQTT listeners.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class IMachineRepository(ABC):
    """Interface for machine/asset registry operations."""

    @abstractmethod
    async def list_machines(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List machines with optional filtering and pagination."""
        ...

    @abstractmethod
    async def get_by_id(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Get machine by unique identifier."""
        ...

    @abstractmethod
    async def get_by_serial(self, serial_number: str) -> Optional[Dict[str, Any]]:
        """Get machine by serial number."""
        ...

    @abstractmethod
    async def create(self, machine_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new machine record."""
        ...

    @abstractmethod
    async def update(self, machine_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update machine information."""
        ...

    @abstractmethod
    async def delete(self, machine_id: str) -> bool:
        """Delete a machine record."""
        ...

    @abstractmethod
    async def get_machine_hierarchy(self, root_id: str) -> Dict[str, Any]:
        """Get machine hierarchy tree."""
        ...


class ITelemetryRepository(ABC):
    """Interface for telemetry/time-series data operations."""

    @abstractmethod
    async def get_latest_telemetry(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent telemetry reading for a machine."""
        ...

    @abstractmethod
    async def get_telemetry_history(
        self,
        machine_id: str,
        start_time: datetime,
        end_time: datetime,
        metrics: Optional[List[str]] = None,
        aggregation: Optional[str] = None,
        interval: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get historical telemetry data with optional aggregation."""
        ...

    @abstractmethod
    async def get_telemetry_statistics(
        self,
        machine_id: str,
        start_time: datetime,
        end_time: datetime,
        metrics: List[str],
    ) -> Dict[str, Any]:
        """Get statistical summaries (min, max, avg, std) for metrics."""
        ...

    @abstractmethod
    async def insert_telemetry_batch(
        self,
        machine_id: str,
        readings: List[Dict[str, Any]],
    ) -> int:
        """Batch insert telemetry readings. Returns count inserted."""
        ...

    @abstractmethod
    async def get_machines_with_recent_telemetry(
        self,
        since: datetime,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get machines that have reported telemetry since given time."""
        ...


class IAlarmRepository(ABC):
    """Interface for alarm/alert management operations."""

    @abstractmethod
    async def get_active_alarms(
        self,
        severity: Optional[str] = None,
        machine_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get active alarms with optional filtering."""
        ...

    @abstractmethod
    async def get_alarm_history(
        self,
        machine_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get alarm history with filtering."""
        ...

    @abstractmethod
    async def get_alarm_by_id(self, alarm_id: str) -> Optional[Dict[str, Any]]:
        """Get alarm by unique identifier."""
        ...

    @abstractmethod
    async def acknowledge_alarm(
        self,
        alarm_id: str,
        user_id: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Acknowledge an active alarm."""
        ...

    @abstractmethod
    async def resolve_alarm(
        self,
        alarm_id: str,
        user_id: str,
        resolution_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Resolve an active alarm."""
        ...

    @abstractmethod
    async def get_alarm_statistics(
        self,
        start_time: datetime,
        end_time: datetime,
        group_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get alarm statistics for dashboard."""
        ...

    @abstractmethod
    async def create_alarm(self, alarm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alarm (called by MQTT listener)."""
        ...


class IMetadataRepository(ABC):
    """Interface for machine metadata and configuration operations."""

    @abstractmethod
    async def get_machine_metadata(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Get extended metadata for a machine."""
        ...

    @abstractmethod
    async def get_machine_sensors(self, machine_id: str) -> List[Dict[str, Any]]:
        """Get sensor definitions for a machine."""
        ...

    @abstractmethod
    async def get_thresholds(self, machine_id: str) -> Dict[str, Any]:
        """Get alarm thresholds for a machine."""
        ...

    @abstractmethod
    async def update_thresholds(
        self,
        machine_id: str,
        thresholds: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update alarm thresholds for a machine."""
        ...

    @abstractmethod
    async def get_maintenance_schedule(self, machine_id: str) -> List[Dict[str, Any]]:
        """Get maintenance schedule for a machine."""
        ...

    @abstractmethod
    async def get_firmware_version(self, machine_id: str) -> Optional[str]:
        """Get current firmware version for a machine."""
        ...

    @abstractmethod
    async def get_machine_documentation(self, machine_id: str) -> List[Dict[str, Any]]:
        """Get documentation links for a machine."""
        ...


class IUserRepository(ABC):
    """Interface for user management operations."""

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        ...

    @abstractmethod
    async def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """List users with pagination. Returns (users, total_count)."""
        ...

    @abstractmethod
    async def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        ...

    @abstractmethod
    async def update(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user."""
        ...

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete user."""
        ...

    @abstractmethod
    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        ...

    @abstractmethod
    async def update_password(self, user_id: str, password_hash: str) -> None:
        """Update user's password hash."""
        ...


class IRoleRepository(ABC):
    """Interface for role management operations."""

    @abstractmethod
    async def get_by_id(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Get role by ID."""
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get role by name."""
        ...

    @abstractmethod
    async def list_roles(self) -> List[Dict[str, Any]]:
        """List all roles."""
        ...

    @abstractmethod
    async def create(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new role."""
        ...

    @abstractmethod
    async def update(self, role_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update role."""
        ...

    @abstractmethod
    async def delete(self, role_id: str) -> bool:
        """Delete role."""
        ...


class IPermissionRepository(ABC):
    """Interface for permission management operations."""

    @abstractmethod
    async def get_by_id(self, perm_id: str) -> Optional[Dict[str, Any]]:
        """Get permission by ID."""
        ...

    @abstractmethod
    async def list_permissions(self) -> List[Dict[str, Any]]:
        """List all permissions."""
        ...

    @abstractmethod
    async def create(self, perm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new permission."""
        ...

    @abstractmethod
    async def update(self, perm_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update permission."""
        ...

    @abstractmethod
    async def delete(self, perm_id: str) -> bool:
        """Delete permission."""
        ...