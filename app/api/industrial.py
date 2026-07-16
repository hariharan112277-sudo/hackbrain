"""
Industrial IoT API Routes
Phase 5: Machine, telemetry, alarm, and metadata endpoints for Member 2 & 4 integration.
"""

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, status, HTTPException

from app.core.security import get_current_user, require_roles, require_permissions
from app.schemas.industrial import (
    MachineResponse,
    MachineCreate,
    MachineUpdate,
    MachineListResponse,
    TelemetryResponse,
    TelemetryHistoryRequest,
    TelemetryStatisticsResponse,
    AlarmResponse,
    AlarmAcknowledgeRequest,
    AlarmResolveRequest,
    AlarmListResponse,
    AlarmStatisticsResponse,
    MachineMetadataResponse,
    SensorDefinition,
    ThresholdConfig,
    AnomalyPredictionRequest,
    AnomalyPredictionResponse,
    RULPredictionRequest,
    RULPredictionResponse,
)
from app.services.industrial_service import IndustrialService
from app.core.dependencies import get_industrial_service

router = APIRouter()


# Machine Routes
@router.get("/machines", response_model=MachineListResponse, summary="List machines")
async def list_machines(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name/serial"),
    current_user: dict = Depends(require_permissions("machines:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """List machines with pagination and filtering."""
    filters = {}
    if status:
        filters["status"] = status
    if search:
        filters["search"] = search
    
    machines = await industrial_service.get_all_machines(
        filters=filters,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    
    # Get total count for pagination
    all_machines = await industrial_service.get_all_machines(filters=filters, limit=1000)
    total = len(all_machines)
    
    return MachineListResponse(
        machines=[MachineResponse(**m) for m in machines],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/machines/{machine_id}", response_model=MachineResponse, summary="Get machine by ID")
async def get_machine(
    machine_id: UUID,
    current_user: dict = Depends(require_permissions("machines:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get machine by ID."""
    machine = await industrial_service.get_machine(machine_id)
    return MachineResponse(**machine)


@router.get("/machines/serial/{serial_number}", response_model=MachineResponse, summary="Get machine by serial")
async def get_machine_by_serial(
    serial_number: str,
    current_user: dict = Depends(require_permissions("machines:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get machine by serial number."""
    machine = await industrial_service.get_machine_by_serial(serial_number)
    return MachineResponse(**machine)


@router.post("/machines", response_model=MachineResponse, status_code=status.HTTP_201_CREATED, summary="Create machine")
async def create_machine(
    machine_data: MachineCreate,
    current_user: dict = Depends(require_permissions("machines:write")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Create a new machine."""
    machine = await industrial_service.create_machine(machine_data)
    return MachineResponse(**machine)


@router.patch("/machines/{machine_id}", response_model=MachineResponse, summary="Update machine")
async def update_machine(
    machine_id: UUID,
    updates: MachineUpdate,
    current_user: dict = Depends(require_permissions("machines:write")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Update machine information."""
    machine = await industrial_service.update_machine(machine_id, updates)
    return MachineResponse(**machine)


@router.delete("/machines/{machine_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete machine")
async def delete_machine(
    machine_id: UUID,
    current_user: dict = Depends(require_permissions("machines:delete")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Delete a machine."""
    await industrial_service.delete_machine(machine_id)


@router.get("/machines/{machine_id}/hierarchy", summary="Get machine hierarchy")
async def get_machine_hierarchy(
    machine_id: UUID,
    current_user: dict = Depends(require_permissions("machines:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get machine hierarchy tree."""
    return await industrial_service.get_machine_hierarchy(machine_id)


# Telemetry Routes
@router.get("/machines/{machine_id}/telemetry", response_model=TelemetryResponse, summary="Get latest telemetry")
async def get_latest_telemetry(
    machine_id: UUID,
    current_user: dict = Depends(require_permissions("telemetry:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get latest telemetry reading for a machine."""
    telemetry = await industrial_service.get_latest_telemetry(machine_id)
    if not telemetry:
        raise HTTPException(status_code=404, detail="No telemetry data found")
    return TelemetryResponse(
        machine_id=machine_id,
        metrics=telemetry.get("metrics", []),
        timestamp=telemetry.get("timestamp", datetime.utcnow()),
    )


@router.get("/machines/{machine_id}/telemetry/flow", summary="Get machine with telemetry and metadata")
async def get_machine_telemetry_flow(
    machine_id: UUID,
    current_user: dict = Depends(require_permissions("telemetry:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get combined machine info, latest telemetry, and metadata."""
    return await industrial_service.get_machine_telemetry_flow(machine_id)


@router.post("/machines/{machine_id}/telemetry/history", response_model=List[TelemetryResponse], summary="Get telemetry history")
async def get_telemetry_history(
    machine_id: UUID,
    request: TelemetryHistoryRequest,
    current_user: dict = Depends(require_permissions("telemetry:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get historical telemetry data with optional aggregation."""
    # Ensure machine_id matches path
    request.machine_id = machine_id
    return await industrial_service.get_telemetry_history(request)


@router.get("/machines/{machine_id}/telemetry/statistics", response_model=TelemetryStatisticsResponse, summary="Get telemetry statistics")
async def get_telemetry_statistics(
    machine_id: UUID,
    start_time: datetime = Query(..., description="Start time"),
    end_time: datetime = Query(..., description="End time"),
    metrics: List[str] = Query(..., description="Metrics to analyze"),
    current_user: dict = Depends(require_permissions("telemetry:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get statistical summaries for metrics."""
    stats = await industrial_service.get_telemetry_statistics(
        machine_id=machine_id,
        start_time=start_time,
        end_time=end_time,
        metrics=metrics,
    )
    return TelemetryStatisticsResponse(**stats)


@router.get("/machines/recent-telemetry", summary="Get machines with recent telemetry")
async def get_machines_with_recent_telemetry(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_permissions("telemetry:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get machines that have reported telemetry recently."""
    since = datetime.utcnow() - timedelta(hours=hours)
    return await industrial_service.get_machines_with_recent_telemetry(since, limit)


# Alarm Routes
@router.get("/alarms", response_model=AlarmListResponse, summary="List active alarms")
async def list_active_alarms(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    machine_id: Optional[UUID] = Query(None, description="Filter by machine"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_permissions("alarms:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """List active alarms with filtering."""
    alarms = await industrial_service.get_active_alarms(
        severity=severity,
        machine_id=machine_id,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    
    # Get total count
    all_alarms = await industrial_service.get_active_alarms(
        severity=severity,
        machine_id=machine_id,
        limit=1000,
    )
    total = len(all_alarms)
    
    return AlarmListResponse(
        alarms=[AlarmResponse(**a) for a in alarms],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/alarms/history", response_model=AlarmListResponse, summary="Get alarm history")
async def get_alarm_history(
    machine_id: Optional[UUID] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_permissions("alarms:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get alarm history with filtering."""
    alarms = await industrial_service.get_alarm_history(
        machine_id=machine_id,
        start_time=start_time,
        end_time=end_time,
        status=status,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    
    all_alarms = await industrial_service.get_alarm_history(
        machine_id=machine_id,
        start_time=start_time,
        end_time=end_time,
        status=status,
        limit=1000,
    )
    total = len(all_alarms)
    
    return AlarmListResponse(
        alarms=[AlarmResponse(**a) for a in alarms],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/alarms/{alarm_id}", response_model=AlarmResponse, summary="Get alarm by ID")
async def get_alarm(
    alarm_id: UUID,
    current_user: dict = Depends(require_permissions("alarms:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get alarm by ID."""
    alarm = await industrial_service.get_alarm(alarm_id)
    return AlarmResponse(**alarm)


@router.post("/alarms/{alarm_id}/acknowledge", response_model=AlarmResponse, summary="Acknowledge alarm")
async def acknowledge_alarm(
    alarm_id: UUID,
    request: AlarmAcknowledgeRequest,
    current_user: dict = Depends(require_permissions("alarms:acknowledge")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Acknowledge an active alarm."""
    from uuid import UUID as UUIDClass
    user_id = UUIDClass(current_user["sub"])
    alarm = await industrial_service.acknowledge_alarm(alarm_id, user_id, request)
    return AlarmResponse(**alarm)


@router.post("/alarms/{alarm_id}/resolve", response_model=AlarmResponse, summary="Resolve alarm")
async def resolve_alarm(
    alarm_id: UUID,
    request: AlarmResolveRequest,
    current_user: dict = Depends(require_permissions("alarms:resolve")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Resolve an active alarm."""
    from uuid import UUID as UUIDClass
    user_id = UUIDClass(current_user["sub"])
    alarm = await industrial_service.resolve_alarm(alarm_id, user_id, request)
    return AlarmResponse(**alarm)


@router.get("/alarms/statistics", response_model=AlarmStatisticsResponse, summary="Get alarm statistics")
async def get_alarm_statistics(
    start_time: datetime = Query(..., description="Start time"),
    end_time: datetime = Query(..., description="End time"),
    group_by: Optional[str] = Query(None, description="Group by field"),
    current_user: dict = Depends(require_permissions("alarms:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get alarm statistics for dashboard."""
    stats = await industrial_service.get_alarm_statistics(
        start_time=start_time,
        end_time=end_time,
        group_by=group_by,
    )
    return AlarmStatisticsResponse(**stats)


# Metadata Routes
@router.get("/machines/{machine_id}/metadata", response_model=MachineMetadataResponse, summary="Get machine metadata")
async def get_machine_metadata(
    machine_id: UUID,
    current_user: dict = Depends(require_permissions("machines:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get complete machine metadata."""
    metadata = await industrial_service.get_machine_metadata(machine_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
    
    sensors = await industrial_service.get_machine_sensors(machine_id)
    thresholds = await industrial_service.get_thresholds(machine_id)
    maintenance = await industrial_service.get_maintenance_schedule(machine_id)
    
    return MachineMetadataResponse(
        machine_id=machine_id,
        sensors=[SensorDefinition(**s) for s in sensors],
        thresholds={k: ThresholdConfig(**v) for k, v in thresholds.items()},
        maintenance_schedule=maintenance,
        firmware_version=metadata.get("firmware_version"),
        documentation=metadata.get("documentation", []),
    )


@router.get("/machines/{machine_id}/sensors", response_model=List[SensorDefinition], summary="Get machine sensors")
async def get_machine_sensors(
    machine_id: UUID,
    current_user: dict = Depends(require_permissions("machines:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get sensor definitions for a machine."""
    sensors = await industrial_service.get_machine_sensors(machine_id)
    return [SensorDefinition(**s) for s in sensors]


@router.get("/machines/{machine_id}/thresholds", response_model=Dict[str, ThresholdConfig], summary="Get alarm thresholds")
async def get_thresholds(
    machine_id: UUID,
    current_user: dict = Depends(require_permissions("machines:read")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Get alarm thresholds for a machine."""
    thresholds = await industrial_service.get_thresholds(machine_id)
    return {k: ThresholdConfig(**v) for k, v in thresholds.items()}


@router.patch("/machines/{machine_id}/thresholds", response_model=Dict[str, ThresholdConfig], summary="Update alarm thresholds")
async def update_thresholds(
    machine_id: UUID,
    thresholds: Dict[str, ThresholdConfig],
    current_user: dict = Depends(require_permissions("machines:write")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Update alarm thresholds for a machine."""
    threshold_dict = {k: v.model_dump() for k, v in thresholds.items()}
    result = await industrial_service.update_thresholds(machine_id, threshold_dict)
    return {k: ThresholdConfig(**v) for k, v in result.items()}


# AI Integration Routes (Member 3 Stubs)
@router.post("/ai/anomaly/predict", response_model=AnomalyPredictionResponse, summary="Predict anomaly")
async def predict_anomaly(
    request: AnomalyPredictionRequest,
    current_user: dict = Depends(require_permissions("ai:predict")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Predict anomaly for machine telemetry (Member 3 integration stub)."""
    return await industrial_service.predict_anomaly(request)


@router.post("/ai/rul/predict", response_model=RULPredictionResponse, summary="Predict RUL")
async def predict_rul(
    request: RULPredictionRequest,
    current_user: dict = Depends(require_permissions("ai:predict")),
    industrial_service: IndustrialService = Depends(get_industrial_service),
):
    """Predict Remaining Useful Life (Member 3 integration stub)."""
    return await industrial_service.predict_rul(request)