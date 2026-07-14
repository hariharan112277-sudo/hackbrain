"""
Repository composition root.

Exposes the abstract interfaces and wires concrete implementations according to
the `PHASE4_REPOSITORY_MODE` setting:
- "stub"    -> in-memory repositories (default, useful for tests / demos)
- "integration" -> adapters backed by the Member 2 integration services
"""
from typing import Any, Callable

from app.core.config import settings
from app.repositories.interfaces import (
    IMachineRepository,
    ITelemetryRepository,
    IAlarmRepository,
    IMetadataRepository,
)
from app.repositories.stubs import build_default_stubs

# Default in-memory stubs are always available.
_STUBS = build_default_stubs()

# Lazy integration adapter loading so the stub path never fails.
_integration_loaded = False
_integration_repos: dict[str, Any] = {}


def _load_integration_repos() -> dict[str, Any]:
    global _integration_loaded, _integration_repos
    if not _integration_loaded:
        from database.connection import connection_manager
        from app.repositories.adapters import (
            IntegrationMachineRepository,
            IntegrationTelemetryRepository,
            IntegrationAlarmRepository,
            IntegrationMetadataRepository,
        )

        _integration_repos = {
            "machine": IntegrationMachineRepository(connection_manager),
            "telemetry": IntegrationTelemetryRepository(connection_manager),
            "alarm": IntegrationAlarmRepository(connection_manager),
            "metadata": IntegrationMetadataRepository(connection_manager),
        }
        _integration_loaded = True
    return _integration_repos


def _repo(name: str) -> Any:
    if settings.PHASE4_REPOSITORY_MODE == "integration":
        return _load_integration_repos()[name]
    return _STUBS[name]


def get_machine_repo() -> IMachineRepository:
    """Return the active machine repository implementation."""
    return _repo("machine")


def get_telemetry_repo() -> ITelemetryRepository:
    """Return the active telemetry repository implementation."""
    return _repo("telemetry")


def get_alarm_repo() -> IAlarmRepository:
    """Return the active alarm repository implementation."""
    return _repo("alarm")


def get_metadata_repo() -> IMetadataRepository:
    """Return the active metadata repository implementation."""
    return _repo("metadata")


__all__ = [
    "IMachineRepository",
    "ITelemetryRepository",
    "IAlarmRepository",
    "IMetadataRepository",
    "get_machine_repo",
    "get_telemetry_repo",
    "get_alarm_repo",
    "get_metadata_repo",
]
