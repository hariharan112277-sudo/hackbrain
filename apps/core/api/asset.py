from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.config import settings
from app.deps import get_current_user, UserContext
from app.services.industrial_service import IndustrialService
from app.core.dependencies import get_industrial_service

router = APIRouter()

@router.get("/", response_model=List[dict])
async def list_assets(
    limit: int = Query(
        settings.DEFAULT_PAGE_LIMIT,
        ge=1,
        le=settings.MAX_PAGE_LIMIT,
        description="Maximum number of assets to return (R-4.2.1: capped at 100)",
    ),
    offset: int = Query(0, ge=0, description="Number of assets to skip"),
    service: IndustrialService = Depends(get_industrial_service),
    user: UserContext = Depends(get_current_user)
):
    """
    Retrieve all assets with their latest status.

    Phase 4 (R-4.2.1): list responses are bounded by an explicit default
    limit of 100 items to safeguard client application memory.
    """
    return await service.get_all_machines(limit=limit, offset=offset)

@router.get("/{asset_id}", response_model=dict)
async def get_asset(
    asset_id: str,
    service: IndustrialService = Depends(get_industrial_service),
    user: UserContext = Depends(get_current_user)
):
    """
    Get detailed information for a specific asset.
    """
    return await service.get_machine_telemetry_flow(asset_id)

@router.get("/{asset_id}/telemetry", response_model=List[dict])
async def get_asset_telemetry(
    asset_id: str,
    range: str = Query("1h", pattern="^(1h|24h|7d)$"),
    service: IndustrialService = Depends(get_industrial_service),
    user: UserContext = Depends(get_current_user)
):
    """
    Get historical telemetry for an asset.
    """
    from app.schemas.industrial import TelemetryHistoryRequest
    from datetime import datetime, timedelta, timezone
    
    delta_map = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
    }
    start_time = datetime.now(timezone.utc) - delta_map[range]
    
    request = TelemetryHistoryRequest(
        machine_id=asset_id,
        start_time=start_time,
        end_time=datetime.now(timezone.utc)
    )
    return await service.get_telemetry_history(request)
