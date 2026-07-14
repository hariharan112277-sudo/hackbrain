"""
Dependency Injection Container
Phase 5: FastAPI dependency providers for services and repositories.
"""

from functools import lru_cache
from typing import Optional
from fastapi import Depends

from app.core.config import settings
from app.repositories.interfaces import (
    IMachineRepository,
    ITelemetryRepository,
    IAlarmRepository,
    IMetadataRepository,
    IUserRepository,
    IRoleRepository,
    IPermissionRepository,
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.industrial_service import IndustrialService
from app.services.dashboard_service import DashboardService


# Repository instances (to be implemented by Member 2)
_machine_repo: Optional[IMachineRepository] = None
_telemetry_repo: Optional[ITelemetryRepository] = None
_alarm_repo: Optional[IAlarmRepository] = None
_metadata_repo: Optional[IMetadataRepository] = None
_user_repo: Optional[IUserRepository] = None
_role_repo: Optional[IRoleRepository] = None
_permission_repo: Optional[IPermissionRepository] = None


def set_repositories(
    machine_repo: IMachineRepository,
    telemetry_repo: ITelemetryRepository,
    alarm_repo: IAlarmRepository,
    metadata_repo: IMetadataRepository,
    user_repo: IUserRepository,
    role_repo: IRoleRepository,
    permission_repo: IPermissionRepository,
) -> None:
    """Set repository implementations (called at startup)."""
    global _machine_repo, _telemetry_repo, _alarm_repo, _metadata_repo
    global _user_repo, _role_repo, _permission_repo
    
    _machine_repo = machine_repo
    _telemetry_repo = telemetry_repo
    _alarm_repo = alarm_repo
    _metadata_repo = metadata_repo
    _user_repo = user_repo
    _role_repo = role_repo
    _permission_repo = permission_repo


def get_machine_repo() -> IMachineRepository:
    if _machine_repo is None:
        raise RuntimeError("Machine repository not initialized")
    return _machine_repo


def get_telemetry_repo() -> ITelemetryRepository:
    if _telemetry_repo is None:
        raise RuntimeError("Telemetry repository not initialized")
    return _telemetry_repo


def get_alarm_repo() -> IAlarmRepository:
    if _alarm_repo is None:
        raise RuntimeError("Alarm repository not initialized")
    return _alarm_repo


def get_metadata_repo() -> IMetadataRepository:
    if _metadata_repo is None:
        raise RuntimeError("Metadata repository not initialized")
    return _metadata_repo


def get_user_repo() -> IUserRepository:
    if _user_repo is None:
        raise RuntimeError("User repository not initialized")
    return _user_repo


def get_role_repo() -> IRoleRepository:
    if _role_repo is None:
        raise RuntimeError("Role repository not initialized")
    return _role_repo


def get_permission_repo() -> IPermissionRepository:
    if _permission_repo is None:
        raise RuntimeError("Permission repository not initialized")
    return _permission_repo


# Service Dependencies
@lru_cache
def get_auth_service() -> AuthService:
    return AuthService(user_repo=get_user_repo())


@lru_cache
def get_user_service() -> UserService:
    return UserService(
        user_repo=get_user_repo(),
        role_repo=get_role_repo(),
        permission_repo=get_permission_repo(),
    )


@lru_cache
def get_industrial_service() -> IndustrialService:
    return IndustrialService(
        machine_repo=get_machine_repo(),
        telemetry_repo=get_telemetry_repo(),
        alarm_repo=get_alarm_repo(),
        metadata_repo=get_metadata_repo(),
    )


@lru_cache
def get_dashboard_service() -> DashboardService:
    return DashboardService(industrial_service=get_industrial_service())


# Repository stub implementations for testing/development
class StubMachineRepository:
    """Stub implementation for development/testing."""
    
    def __init__(self):
        self._machines = {}
    
    async def list_machines(self, filters=None, limit=100, offset=0):
        return list(self._machines.values())[offset:offset+limit]
    
    async def get_by_id(self, machine_id):
        return self._machines.get(machine_id)
    
    async def get_by_serial(self, serial_number):
        for m in self._machines.values():
            if m.get("serial_number") == serial_number:
                return m
        return None
    
    async def create(self, machine_data):
        import uuid
        machine_id = str(uuid.uuid4())
        machine_data["id"] = machine_id
        self._machines[machine_id] = machine_data
        return machine_data
    
    async def update(self, machine_id, updates):
        if machine_id in self._machines:
            self._machines[machine_id].update(updates)
            return self._machines[machine_id]
        return None
    
    async def delete(self, machine_id):
        if machine_id in self._machines:
            del self._machines[machine_id]
            return True
        return False
    
    async def get_machine_hierarchy(self, root_id):
        return {"root": root_id, "children": []}


class StubTelemetryRepository:
    """Stub implementation for development/testing."""
    
    async def get_latest_telemetry(self, machine_id):
        return {
            "machine_id": machine_id,
            "timestamp": "2024-01-15T10:30:00Z",
            "metrics": [
                {"name": "temperature", "value": 75.5, "unit": "°C"},
                {"name": "pressure", "value": 8.2, "unit": "bar"},
                {"name": "vibration", "value": 2.1, "unit": "mm/s"},
            ]
        }
    
    async def get_telemetry_history(self, machine_id, start_time, end_time, metrics=None, aggregation=None, interval=None):
        return []
    
    async def get_telemetry_statistics(self, machine_id, start_time, end_time, metrics):
        return {}
    
    async def insert_telemetry_batch(self, machine_id, readings):
        return len(readings)
    
    async def get_machines_with_recent_telemetry(self, since, limit=100):
        return []


class StubAlarmRepository:
    """Stub implementation for development/testing."""
    
    async def get_active_alarms(self, severity=None, machine_id=None, limit=100, offset=0):
        return []
    
    async def get_alarm_history(self, machine_id=None, start_time=None, end_time=None, status=None, limit=100, offset=0):
        return []
    
    async def get_alarm_by_id(self, alarm_id):
        return None
    
    async def acknowledge_alarm(self, alarm_id, user_id, notes=None):
        return {}
    
    async def resolve_alarm(self, alarm_id, user_id, resolution_notes=None):
        return {}
    
    async def get_alarm_statistics(self, start_time, end_time, group_by=None):
        return {}
    
    async def create_alarm(self, alarm_data):
        return alarm_data


class StubMetadataRepository:
    """Stub implementation for development/testing."""
    
    async def get_machine_metadata(self, machine_id):
        return {"firmware_version": "1.0.0", "documentation": []}
    
    async def get_machine_sensors(self, machine_id):
        return []
    
    async def get_thresholds(self, machine_id):
        return {}
    
    async def update_thresholds(self, machine_id, thresholds):
        return thresholds
    
    async def get_maintenance_schedule(self, machine_id):
        return []
    
    async def get_firmware_version(self, machine_id):
        return "1.0.0"
    
    async def get_machine_documentation(self, machine_id):
        return []


class StubUserRepository:
    """Stub implementation for development/testing."""
    
    def __init__(self):
        self._users = {}
    
    async def get_by_id(self, user_id):
        return self._users.get(user_id)
    
    async def get_by_email(self, email):
        for u in self._users.values():
            if u.get("email") == email:
                return u
        return None
    
    async def list_users(self, limit=100, offset=0, filters=None):
        users = list(self._users.values())[offset:offset+limit]
        return users, len(self._users)
    
    async def create(self, user_data):
        import uuid
        user_id = str(uuid.uuid4())
        user_data["id"] = user_id
        self._users[user_id] = user_data
        return user_data
    
    async def update(self, user_id, updates):
        if user_id in self._users:
            self._users[user_id].update(updates)
            return self._users[user_id]
        return None
    
    async def delete(self, user_id):
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False
    
    async def update_last_login(self, user_id):
        pass
    
    async def update_password(self, user_id, password_hash):
        pass


class StubRoleRepository:
    """Stub implementation for development/testing."""
    
    def __init__(self):
        self._roles = {
            "admin": {"id": "1", "name": "admin", "description": "Administrator", "permissions": ["*"], "is_system": True},
            "manager": {"id": "2", "name": "manager", "description": "Manager", "permissions": ["read", "write"], "is_system": True},
            "operator": {"id": "3", "name": "operator", "description": "Operator", "permissions": ["read"], "is_system": True},
            "viewer": {"id": "4", "name": "viewer", "description": "Viewer", "permissions": ["read"], "is_system": True},
        }
    
    async def get_by_id(self, role_id):
        return self._roles.get(role_id)
    
    async def get_by_name(self, name):
        return self._roles.get(name)
    
    async def list_roles(self):
        return list(self._roles.values())
    
    async def create(self, role_data):
        import uuid
        role_id = str(uuid.uuid4())
        role_data["id"] = role_id
        self._roles[role_data["name"]] = role_data
        return role_data
    
    async def update(self, role_id, updates):
        for name, role in self._roles.items():
            if role["id"] == role_id:
                role.update(updates)
                return role
        return None
    
    async def delete(self, role_id):
        for name, role in list(self._roles.items()):
            if role["id"] == role_id:
                if role.get("is_system"):
                    return False
                del self._roles[name]
                return True
        return False


class StubPermissionRepository:
    """Stub implementation for development/testing."""
    
    def __init__(self):
        self._permissions = {
            "machines:read": {"id": "1", "name": "machines:read", "resource": "machines", "action": "read"},
            "machines:write": {"id": "2", "name": "machines:write", "resource": "machines", "action": "write"},
            "machines:delete": {"id": "3", "name": "machines:delete", "resource": "machines", "action": "delete"},
            "telemetry:read": {"id": "4", "name": "telemetry:read", "resource": "telemetry", "action": "read"},
            "alarms:read": {"id": "5", "name": "alarms:read", "resource": "alarms", "action": "read"},
            "alarms:acknowledge": {"id": "6", "name": "alarms:acknowledge", "resource": "alarms", "action": "acknowledge"},
            "alarms:resolve": {"id": "7", "name": "alarms:resolve", "resource": "alarms", "action": "resolve"},
            "dashboard:read": {"id": "8", "name": "dashboard:read", "resource": "dashboard", "action": "read"},
            "ai:predict": {"id": "9", "name": "ai:predict", "resource": "ai", "action": "predict"},
        }
    
    async def get_by_id(self, perm_id):
        return self._permissions.get(perm_id)
    
    async def list_permissions(self):
        return list(self._permissions.values())
    
    async def create(self, perm_data):
        import uuid
        perm_id = str(uuid.uuid4())
        perm_data["id"] = perm_id
        self._permissions[perm_data["name"]] = perm_data
        return perm_data
    
    async def update(self, perm_id, updates):
        for name, perm in self._permissions.items():
            if perm["id"] == perm_id:
                perm.update(updates)
                return perm
        return None
    
    async def delete(self, perm_id):
        for name, perm in list(self._permissions.items()):
            if perm["id"] == perm_id:
                del self._permissions[name]
                return True
        return False


def initialize_stub_repositories() -> None:
    """Initialize stub repositories for development/testing."""
    set_repositories(
        machine_repo=StubMachineRepository(),
        telemetry_repo=StubTelemetryRepository(),
        alarm_repo=StubAlarmRepository(),
        metadata_repo=StubMetadataRepository(),
        user_repo=StubUserRepository(),
        role_repo=StubRoleRepository(),
        permission_repo=StubPermissionRepository(),
    )