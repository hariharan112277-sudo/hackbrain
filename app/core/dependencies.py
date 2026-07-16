"""Repository and service dependency-injection runtime gates."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from functools import lru_cache
from threading import RLock
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

from app.core.config import settings
from app.repositories.interfaces import (
    IAlarmRepository,
    IMachineRepository,
    IMetadataRepository,
    IPermissionRepository,
    IRoleRepository,
    ITelemetryRepository,
    IUserRepository,
)
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.industrial_service import IndustrialService
from app.services.user_service import UserService

logger = logging.getLogger("app.core.dependencies")
_repository_lock = RLock()

_machine_repository: Optional[IMachineRepository] = None
_telemetry_repository: Optional[ITelemetryRepository] = None
_alarm_repository: Optional[IAlarmRepository] = None
_metadata_repository: Optional[IMetadataRepository] = None
_user_repository: Optional[IUserRepository] = None
_role_repository: Optional[IRoleRepository] = None
_permission_repository: Optional[IPermissionRepository] = None
_repository_mode: Optional[str] = None


def _clear_service_caches() -> None:
    get_auth_service.cache_clear()
    get_user_service.cache_clear()
    get_industrial_service.cache_clear()
    get_dashboard_service.cache_clear()


def _looks_like_stub(repository: object) -> bool:
    class_name = repository.__class__.__name__.lower()
    module_name = repository.__class__.__module__.lower()
    return (
        class_name.startswith("stub")
        or class_name.startswith("inmemory")
        or module_name.endswith(".stubs")
    )


def set_repositories(
    machine_repo: IMachineRepository,
    telemetry_repo: ITelemetryRepository,
    alarm_repo: IAlarmRepository,
    metadata_repo: IMetadataRepository,
    user_repo: IUserRepository,
    role_repo: IRoleRepository,
    permission_repo: IPermissionRepository,
) -> None:
    """Install an explicitly supplied repository set.

    Production rejects classes that identify as stub or in-memory providers,
    preventing application setup hooks from bypassing the normal runtime gate.
    """
    repositories = (
        machine_repo,
        telemetry_repo,
        alarm_repo,
        metadata_repo,
        user_repo,
        role_repo,
        permission_repo,
    )
    if settings.is_production and any(_looks_like_stub(repo) for repo in repositories):
        raise RuntimeError(
            "CRITICAL ARCHITECTURAL FAILURE: Stub repositories are strictly "
            "forbidden in production."
        )

    global _machine_repository, _telemetry_repository, _alarm_repository
    global _metadata_repository, _user_repository, _role_repository
    global _permission_repository, _repository_mode

    with _repository_lock:
        _machine_repository = machine_repo
        _telemetry_repository = telemetry_repo
        _alarm_repository = alarm_repo
        _metadata_repository = metadata_repo
        _user_repository = user_repo
        _role_repository = role_repo
        _permission_repository = permission_repo
        _repository_mode = "external"
        _clear_service_caches()


class StubMachineRepository(IMachineRepository):
    """Volatile machine repository for tests and local development."""

    def __init__(self) -> None:
        self._machines: Dict[str, Dict[str, Any]] = {}

    async def list_machines(self, filters=None, limit=100, offset=0):
        machines = list(self._machines.values())
        if filters:
            machines = [
                machine
                for machine in machines
                if all(machine.get(key) == value for key, value in filters.items())
            ]
        return machines[offset : offset + limit]

    async def get_by_id(self, machine_id):
        return self._machines.get(str(machine_id))

    async def get_by_serial(self, serial_number):
        return next(
            (
                machine
                for machine in self._machines.values()
                if machine.get("serial_number") == serial_number
            ),
            None,
        )

    async def create(self, machine_data):
        machine = dict(machine_data)
        requested_id = machine.get("id")
        machine_id = uuid4() if not requested_id or str(requested_id) == str(UUID(int=0)) else requested_id
        machine["id"] = machine_id
        self._machines[str(machine_id)] = machine
        return machine

    async def update(self, machine_id, updates):
        machine = self._machines.get(str(machine_id))
        if machine is None:
            return None
        machine.update(updates)
        return machine

    async def delete(self, machine_id):
        return self._machines.pop(str(machine_id), None) is not None

    async def get_machine_hierarchy(self, root_id):
        return {"root": str(root_id), "children": []}


class StubTelemetryRepository(ITelemetryRepository):
    """Deterministic telemetry repository for non-production contexts."""

    def __init__(self) -> None:
        self._readings: Dict[str, List[Dict[str, Any]]] = {}

    async def get_latest_telemetry(self, machine_id):
        readings = self._readings.get(str(machine_id), [])
        if readings:
            return readings[-1]
        return {
            "machine_id": str(machine_id),
            "timestamp": datetime.now(timezone.utc),
            "metrics": [
                {"name": "temperature", "value": 75.5, "unit": "°C"},
                {"name": "pressure", "value": 8.2, "unit": "bar"},
                {"name": "vibration", "value": 2.1, "unit": "mm/s"},
            ],
        }

    async def get_telemetry_history(
        self,
        machine_id,
        start_time,
        end_time,
        metrics=None,
        aggregation=None,
        interval=None,
    ):
        return [
            reading
            for reading in self._readings.get(str(machine_id), [])
            if start_time <= reading["timestamp"] <= end_time
        ]

    async def get_telemetry_statistics(self, machine_id, start_time, end_time, metrics):
        return {}

    async def insert_telemetry_batch(self, machine_id, readings):
        store = self._readings.setdefault(str(machine_id), [])
        store.extend(dict(reading) for reading in readings)
        return len(readings)

    async def get_machines_with_recent_telemetry(self, since, limit=100):
        machine_ids = [
            machine_id
            for machine_id, readings in self._readings.items()
            if any(reading.get("timestamp", since) >= since for reading in readings)
        ]
        return machine_ids[:limit]


class StubAlarmRepository(IAlarmRepository):
    """Volatile alarm repository for non-production contexts."""

    def __init__(self) -> None:
        self._alarms: Dict[str, Dict[str, Any]] = {}

    async def get_active_alarms(
        self,
        severity=None,
        machine_id=None,
        limit=100,
        offset=0,
    ):
        alarms = [alarm for alarm in self._alarms.values() if alarm.get("status") != "resolved"]
        if severity:
            alarms = [alarm for alarm in alarms if alarm.get("severity") == severity]
        if machine_id:
            alarms = [alarm for alarm in alarms if str(alarm.get("machine_id")) == str(machine_id)]
        return alarms[offset : offset + limit]

    async def get_alarm_history(
        self,
        machine_id=None,
        start_time=None,
        end_time=None,
        status=None,
        limit=100,
        offset=0,
    ):
        alarms = list(self._alarms.values())
        if machine_id:
            alarms = [alarm for alarm in alarms if str(alarm.get("machine_id")) == str(machine_id)]
        if status:
            alarms = [alarm for alarm in alarms if alarm.get("status") == status]
        return alarms[offset : offset + limit]

    async def get_alarm_by_id(self, alarm_id):
        return self._alarms.get(str(alarm_id))

    async def acknowledge_alarm(self, alarm_id, user_id, notes=None):
        alarm = self._alarms.get(str(alarm_id))
        if alarm is None:
            return {}
        alarm.update({"status": "acknowledged", "acknowledged_by": str(user_id), "notes": notes})
        return alarm

    async def resolve_alarm(self, alarm_id, user_id, resolution_notes=None):
        alarm = self._alarms.get(str(alarm_id))
        if alarm is None:
            return {}
        alarm.update(
            {
                "status": "resolved",
                "resolved_by": str(user_id),
                "resolution_notes": resolution_notes,
            }
        )
        return alarm

    async def get_alarm_statistics(self, start_time, end_time, group_by=None):
        return {"total": len(self._alarms)}

    async def create_alarm(self, alarm_data):
        alarm = dict(alarm_data)
        alarm_id = alarm.get("id") or uuid4()
        alarm["id"] = alarm_id
        self._alarms[str(alarm_id)] = alarm
        return alarm


class StubMetadataRepository(IMetadataRepository):
    """Static metadata provider for non-production contexts."""

    async def get_machine_metadata(self, machine_id):
        return {"machine_id": str(machine_id), "firmware_version": "1.0.0", "documentation": []}

    async def get_machine_sensors(self, machine_id):
        return []

    async def get_thresholds(self, machine_id):
        return {}

    async def update_thresholds(self, machine_id, thresholds):
        return dict(thresholds)

    async def get_maintenance_schedule(self, machine_id):
        return []

    async def get_firmware_version(self, machine_id):
        return "1.0.0"

    async def get_machine_documentation(self, machine_id):
        return []


class StubUserRepository(IUserRepository):
    """Volatile user repository for tests and local development."""

    def __init__(self) -> None:
        self._users: Dict[str, Dict[str, Any]] = {}

    async def get_by_id(self, user_id):
        return self._users.get(str(user_id))

    async def get_by_email(self, email):
        normalized = str(email).casefold()
        return next(
            (
                user
                for user in self._users.values()
                if str(user.get("email", "")).casefold() == normalized
            ),
            None,
        )

    async def list_users(self, limit=100, offset=0, filters=None):
        users = list(self._users.values())
        active_filters = filters or {}
        if active_filters.get("search"):
            search = str(active_filters["search"]).casefold()
            users = [
                user
                for user in users
                if search in str(user.get("email", "")).casefold()
                or search in str(user.get("full_name", "")).casefold()
            ]
        if active_filters.get("role"):
            users = [user for user in users if active_filters["role"] in user.get("roles", [])]
        if active_filters.get("is_active") is not None:
            users = [
                user
                for user in users
                if user.get("is_active", True) is active_filters["is_active"]
            ]
        return users[offset : offset + limit], len(users)

    async def create(self, user_data):
        user = dict(user_data)
        requested_id = user.get("id")
        user_id = uuid4() if not requested_id or str(requested_id) == str(UUID(int=0)) else requested_id
        now = datetime.now(timezone.utc)
        user.update(
            {
                "id": user_id,
                "created_at": user.get("created_at", now),
                "updated_at": user.get("updated_at", now),
                "last_login": user.get("last_login"),
            }
        )
        self._users[str(user_id)] = user
        return user

    async def update(self, user_id, updates):
        user = self._users.get(str(user_id))
        if user is None:
            return None
        user.update(updates)
        user["updated_at"] = datetime.now(timezone.utc)
        return user

    async def delete(self, user_id):
        return self._users.pop(str(user_id), None) is not None

    async def update_last_login(self, user_id):
        user = self._users.get(str(user_id))
        if user is not None:
            user["last_login"] = datetime.now(timezone.utc)

    async def update_password(self, user_id, password_hash):
        user = self._users.get(str(user_id))
        if user is not None:
            user["password_hash"] = password_hash
            user["updated_at"] = datetime.now(timezone.utc)


class StubRoleRepository(IRoleRepository):
    """Volatile role repository with built-in local policy data."""

    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        self._roles: Dict[str, Dict[str, Any]] = {}
        for name, permissions in {
            "admin": ["*"],
            "manager": ["read", "write"],
            "engineer": ["read", "write"],
            "operator": ["read"],
            "viewer": ["read"],
        }.items():
            self._roles[name] = {
                "id": uuid5(NAMESPACE_URL, f"iob-local-role:{name}"),
                "name": name,
                "description": f"Built-in {name} role",
                "permissions": permissions,
                "created_at": now,
                "is_system": True,
            }

    async def get_by_id(self, role_id):
        return next(
            (role for role in self._roles.values() if str(role["id"]) == str(role_id)),
            None,
        )

    async def get_by_name(self, name):
        return self._roles.get(name)

    async def list_roles(self):
        return list(self._roles.values())

    async def create(self, role_data):
        role = dict(role_data)
        role.update(
            {
                "id": uuid4(),
                "created_at": datetime.now(timezone.utc),
                "is_system": False,
            }
        )
        self._roles[role["name"]] = role
        return role

    async def update(self, role_id, updates):
        role = await self.get_by_id(role_id)
        if role is None:
            return None
        role.update(updates)
        return role

    async def delete(self, role_id):
        role = await self.get_by_id(role_id)
        if role is None or role.get("is_system"):
            return False
        del self._roles[role["name"]]
        return True


class StubPermissionRepository(IPermissionRepository):
    """Volatile permission catalogue for non-production contexts."""

    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        names = (
            "machines:read",
            "machines:write",
            "machines:delete",
            "telemetry:read",
            "alarms:read",
            "alarms:acknowledge",
            "alarms:resolve",
            "dashboard:read",
            "ai:predict",
        )
        self._permissions = {
            name: {
                "id": uuid5(NAMESPACE_URL, f"iob-local-permission:{name}"),
                "name": name,
                "resource": name.split(":", maxsplit=1)[0],
                "action": name.split(":", maxsplit=1)[1],
                "description": None,
                "created_at": now,
            }
            for name in names
        }

    async def get_by_id(self, perm_id):
        return next(
            (
                permission
                for permission in self._permissions.values()
                if str(permission["id"]) == str(perm_id)
            ),
            None,
        )

    async def list_permissions(self):
        return list(self._permissions.values())

    async def create(self, perm_data):
        permission = dict(perm_data)
        permission.update({"id": uuid4(), "created_at": datetime.now(timezone.utc)})
        self._permissions[permission["name"]] = permission
        return permission

    async def update(self, perm_id, updates):
        permission = await self.get_by_id(perm_id)
        if permission is None:
            return None
        permission.update(updates)
        return permission

    async def delete(self, perm_id):
        permission = await self.get_by_id(perm_id)
        if permission is None:
            return False
        del self._permissions[permission["name"]]
        return True


def initialize_stub_repositories() -> None:
    """Allocate volatile repositories after enforcing the production gate."""
    if settings.is_production:
        raise RuntimeError(
            "CRITICAL ARCHITECTURAL FAILURE: Initialization of stub repositories "
            "is strictly forbidden in production."
        )

    logger.warning("Allocating transient in-memory repository providers")
    set_repositories(
        machine_repo=StubMachineRepository(),
        telemetry_repo=StubTelemetryRepository(),
        alarm_repo=StubAlarmRepository(),
        metadata_repo=StubMetadataRepository(),
        user_repo=StubUserRepository(),
        role_repo=StubRoleRepository(),
        permission_repo=StubPermissionRepository(),
    )
    global _repository_mode
    _repository_mode = "stub"


def initialize_production_repositories() -> None:
    """Bind persistent user storage and immutable authorization policy adapters."""
    if settings.USE_STUB_REPOSITORIES:
        raise RuntimeError(
            "CRITICAL ARCHITECTURAL FAILURE: Production repository initialization "
            "requires USE_STUB_REPOSITORIES=false."
        )
    if not settings.DATABASE_URL or not settings.DATABASE_URL.strip():
        raise RuntimeError("DATABASE_URL is required for persistent repositories")

    from app.database import SessionLocal
    from app.repositories.production import (
        PolicyPermissionRepository,
        PolicyRoleRepository,
        SQLAlchemyUserRepository,
    )

    global _machine_repository, _telemetry_repository, _alarm_repository
    global _metadata_repository, _user_repository, _role_repository
    global _permission_repository, _repository_mode

    with _repository_lock:
        # Explicitly clear every volatile industrial provider when changing
        # strategy. Those adapters must be supplied by the database integration
        # owner through set_repositories before their service is requested.
        _machine_repository = None
        _telemetry_repository = None
        _alarm_repository = None
        _metadata_repository = None
        _user_repository = SQLAlchemyUserRepository(SessionLocal)
        _role_repository = PolicyRoleRepository()
        _permission_repository = PolicyPermissionRepository()
        _repository_mode = "production"
        _clear_service_caches()

    logger.info("Persistent repository providers initialized")


def bootstrap_repository_subsystem() -> None:
    """Select and initialize the configured repository strategy."""
    expected_mode = "stub" if settings.USE_STUB_REPOSITORIES else "production"
    if _repository_mode == expected_mode:
        if settings.is_production and _repository_mode == "stub":
            raise RuntimeError(
                "CRITICAL ARCHITECTURAL FAILURE: A stub repository set is active in production."
            )
        return

    if settings.USE_STUB_REPOSITORIES:
        initialize_stub_repositories()
    else:
        initialize_production_repositories()


def reset_repository_subsystem() -> None:
    """Clear providers and cached services; intended for controlled test teardown."""
    global _machine_repository, _telemetry_repository, _alarm_repository
    global _metadata_repository, _user_repository, _role_repository
    global _permission_repository, _repository_mode

    with _repository_lock:
        _machine_repository = None
        _telemetry_repository = None
        _alarm_repository = None
        _metadata_repository = None
        _user_repository = None
        _role_repository = None
        _permission_repository = None
        _repository_mode = None
        _clear_service_caches()


def shutdown_repository_subsystem() -> None:
    """Release repository references and dispose persistent connection pools."""
    mode = _repository_mode
    reset_repository_subsystem()
    if mode == "production":
        from app.database import engine

        engine.dispose()


def _required(repository: Optional[Any], name: str) -> Any:
    if repository is None:
        bootstrap_repository_subsystem()
        repository = globals()[f"_{name}_repository"]
    if repository is None:
        raise RuntimeError(
            f"{name.capitalize()} repository is not initialized for the active strategy"
        )
    return repository


def get_machine_repo() -> IMachineRepository:
    return _required(_machine_repository, "machine")


def get_telemetry_repo() -> ITelemetryRepository:
    return _required(_telemetry_repository, "telemetry")


def get_alarm_repo() -> IAlarmRepository:
    return _required(_alarm_repository, "alarm")


def get_metadata_repo() -> IMetadataRepository:
    return _required(_metadata_repository, "metadata")


def get_user_repo() -> IUserRepository:
    return _required(_user_repository, "user")


def get_role_repo() -> IRoleRepository:
    return _required(_role_repository, "role")


def get_permission_repo() -> IPermissionRepository:
    return _required(_permission_repository, "permission")


async def get_user_repository() -> AsyncGenerator[IUserRepository, None]:
    """FastAPI dependency yielding a fully initialized user repository."""
    yield get_user_repo()


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


__all__ = [
    "bootstrap_repository_subsystem",
    "get_alarm_repo",
    "get_auth_service",
    "get_dashboard_service",
    "get_industrial_service",
    "get_machine_repo",
    "get_metadata_repo",
    "get_permission_repo",
    "get_role_repo",
    "get_telemetry_repo",
    "get_user_repo",
    "get_user_repository",
    "get_user_service",
    "initialize_production_repositories",
    "initialize_stub_repositories",
    "reset_repository_subsystem",
    "set_repositories",
    "shutdown_repository_subsystem",
]
