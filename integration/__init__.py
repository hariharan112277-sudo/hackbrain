"""
Industrial Operating Brain (IOB): Phase 6 — Complete Integration Layer.
Provides clean service abstractions and strongly typed Pydantic V2 DTOs for Member 1 Application Backend.
"""

from .exceptions import (
    IOBIntegrationException,
    ResourceNotFoundError,
    MQTTTransportException,
    DatabaseUnavailableException,
    InvalidQueryCriteriaException,
    ConfigurationValidationException
)
from .config import IntegrationSettings, integration_config
from .contracts import (
    OperationalStatus,
    AlarmSeverity,
    AlarmState,
    BaseDTO,
    AssetDTO,
    MachineDTO,
    SensorDTO,
    TelemetryDTO,
    AlarmDTO,
    MachineEventDTO,
    MaintenanceLogDTO,
    QueryCriteriaDTO,
    AggregatedStatisticsDTO
)
from .interfaces import (
    IMachineRepository,
    ISensorRepository,
    ITelemetryRepository,
    IAlarmRepository,
    IEventRepository,
    IMaintenanceRepository,
    IAssetRepository,
    IMachineRegistryService,
    ISensorRegistryService,
    IHistoricalQueryService,
    IMQTTIntegrationService,
    ITelemetryIntegrationService,
    IAssetIntegrationService,
    IMetadataIntegrationService
)
from .mappers import EntityDTOMapper
from .services import (
    MachineRegistryService,
    SensorRegistryService,
    HistoricalQueryService,
    MQTTIntegrationService,
    TelemetryIntegrationService,
    AssetIntegrationService,
    MetadataIntegrationService
)

__version__ = "6.0.0-INT"
__all__ = [
    "IOBIntegrationException", "ResourceNotFoundError", "MQTTTransportException",
    "DatabaseUnavailableException", "InvalidQueryCriteriaException", "ConfigurationValidationException",
    "IntegrationSettings", "integration_config",
    "OperationalStatus", "AlarmSeverity", "AlarmState", "BaseDTO",
    "AssetDTO", "MachineDTO", "SensorDTO", "TelemetryDTO", "AlarmDTO",
    "MachineEventDTO", "MaintenanceLogDTO", "QueryCriteriaDTO", "AggregatedStatisticsDTO",
    "IMachineRepository", "ISensorRepository", "ITelemetryRepository", "IAlarmRepository",
    "IEventRepository", "IMaintenanceRepository", "IAssetRepository",
    "IMachineRegistryService", "ISensorRegistryService", "IHistoricalQueryService",
    "IMQTTIntegrationService", "ITelemetryIntegrationService", "IAssetIntegrationService",
    "IMetadataIntegrationService",
    "EntityDTOMapper", "MachineRegistryService", "SensorRegistryService",
    "HistoricalQueryService", "MQTTIntegrationService", "TelemetryIntegrationService",
    "AssetIntegrationService", "MetadataIntegrationService"
]
