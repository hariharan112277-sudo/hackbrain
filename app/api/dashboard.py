"""
Dashboard API Routes
Phase 5: Aggregated data endpoints for Member 4 Frontend UI components.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user, require_permissions
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardFilterRequest,
    RealtimeTelemetrySubscription,
    RealtimeTelemetryMessage,
)
from app.services.dashboard_service import DashboardService
from app.core.dependencies import get_dashboard_service

router = APIRouter()


@router.get("/overview", response_model=DashboardOverviewResponse, summary="Get dashboard overview")
async def get_dashboard_overview(
    machine_ids: Optional[list[UUID]] = Query(None, description="Filter by machine IDs"),
    site_ids: Optional[list[str]] = Query(None, description="Filter by site IDs"),
    time_range: str = Query("24h", description="Time range (1h, 6h, 24h, 7d, 30d)"),
    current_user: dict = Depends(require_permissions("dashboard:read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """Get complete dashboard overview with all widgets."""
    filters = DashboardFilterRequest(
        machine_ids=machine_ids,
        site_ids=site_ids,
        time_range=time_range,
    )
    return await dashboard_service.get_overview(filters)


@router.get("/machines/{machine_id}/detail", summary="Get machine detail dashboard")
async def get_machine_detail_dashboard(
    machine_id: UUID,
    current_user: dict = Depends(require_permissions("dashboard:read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """Get detailed dashboard for a single machine."""
    return await dashboard_service.get_machine_detail_dashboard(machine_id)


@router.get("/kpis", summary="Get KPI widgets only")
async def get_kpi_widgets(
    machine_ids: Optional[list[UUID]] = Query(None),
    current_user: dict = Depends(require_permissions("dashboard:read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """Get KPI widgets for dashboard."""
    from app.schemas.dashboard import DashboardFilterRequest
    filters = DashboardFilterRequest(machine_ids=machine_ids)
    overview = await dashboard_service.get_overview(filters)
    return {"kpis": overview.kpi_widgets}


@router.get("/alarms/summary", summary="Get alarm summary widget")
async def get_alarm_summary(
    machine_ids: Optional[list[UUID]] = Query(None),
    current_user: dict = Depends(require_permissions("dashboard:read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """Get alarm summary widget data."""
    from app.schemas.dashboard import DashboardFilterRequest
    filters = DashboardFilterRequest(machine_ids=machine_ids)
    overview = await dashboard_service.get_overview(filters)
    return {"alarms": overview.alarm_widget}


@router.get("/telemetry/widgets", summary="Get telemetry widgets")
async def get_telemetry_widgets(
    machine_ids: Optional[list[UUID]] = Query(None),
    current_user: dict = Depends(require_permissions("dashboard:read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """Get telemetry widget data."""
    from app.schemas.dashboard import DashboardFilterRequest
    filters = DashboardFilterRequest(machine_ids=machine_ids)
    overview = await dashboard_service.get_overview(filters)
    return {"telemetry": overview.telemetry_widgets}


@router.get("/trends", summary="Get trend widgets")
async def get_trend_widgets(
    machine_ids: Optional[list[UUID]] = Query(None),
    current_user: dict = Depends(require_permissions("dashboard:read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """Get trend widget data."""
    from app.schemas.dashboard import DashboardFilterRequest
    filters = DashboardFilterRequest(machine_ids=machine_ids)
    overview = await dashboard_service.get_overview(filters)
    return {"trends": overview.trend_widgets}


@router.get("/machine-status", summary="Get machine status summary")
async def get_machine_status(
    machine_ids: Optional[list[UUID]] = Query(None),
    current_user: dict = Depends(require_permissions("dashboard:read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """Get machine status summary."""
    from app.schemas.dashboard import DashboardFilterRequest
    filters = DashboardFilterRequest(machine_ids=machine_ids)
    overview = await dashboard_service.get_overview(filters)
    return {"status": overview.machine_status}


# WebSocket endpoint for real-time telemetry (placeholder)
@router.websocket("/ws/telemetry")
async def websocket_telemetry(websocket, token: str = Query(...)):
    """
    WebSocket endpoint for real-time telemetry streaming.
    Phase 5: Placeholder - requires WebSocket implementation.
    """
    # TODO: Implement WebSocket authentication and real-time streaming
    await websocket.accept()
    await websocket.send_json({
        "type": "info",
        "message": "WebSocket endpoint not fully implemented in Phase 5",
    })
    await websocket.close()