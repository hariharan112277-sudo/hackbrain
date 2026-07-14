"""
Dashboard REST controller.
"""
from fastapi import APIRouter, Depends

from app.schemas.dashboard import DashboardSummary, KPIMetrics
from app.services.dashboard_service import DashboardService
from app.api.industrial import get_machine_repo, get_alarm_repo
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service(
    m=Depends(get_machine_repo),
    a=Depends(get_alarm_repo),
) -> DashboardService:
    return DashboardService(m, a)


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    service: DashboardService = Depends(get_dashboard_service),
    current_user: dict = Depends(get_current_user),
):
    """Return the aggregated dashboard summary."""
    return await service.compile_dashboard_summary()


@router.get("/kpis", response_model=KPIMetrics)
async def kpis(
    service: DashboardService = Depends(get_dashboard_service),
    current_user: dict = Depends(get_current_user),
):
    """Return industrial Digital Twin KPIs."""
    return await service.get_kpis()
