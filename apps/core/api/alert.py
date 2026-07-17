from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.config import settings
from app.deps import get_current_user, UserContext, require_role
from app.services.industrial_service import IndustrialService
from app.core.dependencies import get_industrial_service
from app.schemas.industrial import AlarmResolveRequest, AlarmAcknowledgeRequest

router = APIRouter()

@router.get("/", response_model=List[dict])
async def list_alerts(
    severity: Optional[str] = Query(None, pattern="^(critical|warning|info)$"),
    limit: int = Query(
        settings.DEFAULT_PAGE_LIMIT,
        ge=1,
        le=settings.MAX_PAGE_LIMIT,
        description="Maximum number of alerts to return (R-4.2.1: capped at 100)",
    ),
    offset: int = Query(0, ge=0, description="Number of alerts to skip"),
    service: IndustrialService = Depends(get_industrial_service),
    user: UserContext = Depends(get_current_user)
):
    """
    Retrieve active alerts with optional severity filtering.

    Phase 4 (R-4.2.1): list responses are bounded by an explicit default
    limit of 100 items to safeguard client application memory.
    """
    return await service.get_active_alarms(severity=severity, limit=limit, offset=offset)

@router.post("/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_alert(
    alert_id: str,
    request: AlarmAcknowledgeRequest,
    service: IndustrialService = Depends(get_industrial_service),
    user: UserContext = Depends(get_current_user)
):
    """
    Acknowledge an active alert.
    """
    return await service.acknowledge_alarm(alert_id, user.user_id, request)

@router.post("/{alert_id}/resolve", response_model=dict)
async def resolve_alert(
    alert_id: str,
    request: AlarmResolveRequest,
    service: IndustrialService = Depends(get_industrial_service),
    user: UserContext = Depends(require_role("admin", "engineer"))
):
    """
    Resolve an alert (Admin/Engineer only).
    """
    return await service.resolve_alarm(alert_id, user.user_id, request)
