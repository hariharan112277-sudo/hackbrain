from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.deps import get_current_user, UserContext
from app.services.industrial_service import IndustrialService
from app.core.dependencies import get_industrial_service

router = APIRouter()

@router.get("/", response_model=List[dict])
async def list_assets(
    service: IndustrialService = Depends(get_industrial_service),
    user: UserContext = Depends(get_current_user)
):
    """
    Retrieve all assets with their latest status.
    """
    return await service.get_all_machines()

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
    range: str = Query("1h", regex="^(1h|24h|7d)$"),
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
