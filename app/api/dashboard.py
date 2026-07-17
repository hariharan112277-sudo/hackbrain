"""Central health KPI endpoint — Track A (Hariharan), Stage 3."""

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import UserContext, get_current_user
from app.core.timeutils import utc_iso  # Phase 4 (R-4.4.1)
from app.models.alarm import Alarm
from app.models.asset import Asset, Telemetry

router = APIRouter()


@router.get("/summary")
def get_dashboard_summary(
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compute aggregate system KPIs and latest machine-state allocations.

    Health formula: max(0, 100 - (10 * critical_open) - (3 * warning_open)).
    """
    total_assets = db.query(func.count(Asset.asset_id)).scalar() or 0

    critical_open = (
        db.query(func.count(Alarm.alarm_id))
        .filter(Alarm.severity == "critical", Alarm.resolved.is_(False))
        .scalar()
        or 0
    )
    warning_open = (
        db.query(func.count(Alarm.alarm_id))
        .filter(Alarm.severity == "warning", Alarm.resolved.is_(False))
        .scalar()
        or 0
    )

    health_score = max(0, 100 - (10 * critical_open) - (3 * warning_open))

    recent_alarms = db.query(Alarm).order_by(desc(Alarm.ts), desc(Alarm.alarm_id)).limit(5).all()

    # Rank by timestamp and then primary key so duplicate timestamps still
    # produce exactly one latest telemetry row per asset.
    latest_telemetry = db.query(
        Telemetry.asset_id.label("asset_id"),
        Telemetry.status.label("status"),
        func.row_number()
        .over(
            partition_by=Telemetry.asset_id,
            order_by=(Telemetry.ts.desc(), Telemetry.id.desc()),
        )
        .label("row_number"),
    ).subquery()

    status_counts = (
        db.query(latest_telemetry.c.status, func.count(Asset.asset_id))
        .select_from(Asset)
        .outerjoin(
            latest_telemetry,
            (Asset.asset_id == latest_telemetry.c.asset_id) & (latest_telemetry.c.row_number == 1),
        )
        .group_by(latest_telemetry.c.status)
        .all()
    )

    machine_status = {}
    for telemetry_status, count in status_counts:
        status_key = telemetry_status or "unknown"
        machine_status[status_key] = machine_status.get(status_key, 0) + count

    return {
        "kpis": {
            "total_assets": total_assets,
            "open_critical_alarms": critical_open,
            "open_warning_alarms": warning_open,
        },
        "health_score": health_score,
        "machine_status": machine_status,
        "recent_alerts": [
            {
                "alarm_id": alarm.alarm_id,
                "asset_id": alarm.asset_id,
                "severity": alarm.severity,
                "message": alarm.message,
                "ts": utc_iso(alarm.ts),
            }
            for alarm in recent_alarms
        ],
    }
