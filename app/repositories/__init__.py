"""
Repository Layer Interfaces
Phase 5: Abstract interfaces for Member 2's IoT and Database layer integration.
"""

from app.repositories.interfaces import (
    IMachineRepository,
    ITelemetryRepository,
    IAlarmRepository,
    IMetadataRepository,
    IUserRepository,
    IRoleRepository,
    IPermissionRepository,
)

__all__ = [
    "IMachineRepository",
    "ITelemetryRepository",
    "IAlarmRepository",
    "IMetadataRepository",
    "IUserRepository",
    "IRoleRepository",
    "IPermissionRepository",
]