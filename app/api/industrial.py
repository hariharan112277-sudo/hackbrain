"""Core industrial REST endpoints — Track A (Hariharan), Stage 3."""

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, status, HTTPException

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.errors import error_envelope
from app.database import get_db
from app.deps import UserContext, get_current_user, require_role
from app.models.alarm import Alarm
from app.models.asset import Asset, Telemetry

router = APIRouter()


def _as_float(value):
    """Convert SQL numeric values to JSON-safe floats without losing zeroes."""
    return float(value) if value is not None else None


def _latest_telemetry_subquery(db: Session):
    """Return one deterministically ranked latest telemetry row per asset."""
    return db.query(
        Telemetry.asset_id.label("asset_id"),
        Telemetry.status.label("status"),
        func.row_number()
        .over(
            partition_by=Telemetry.asset_id,
            order_by=(Telemetry.ts.desc(), Telemetry.id.desc()),
        )
        .label("row_number"),
    ).subquery()


@router.get("/assets")
def get_assets(
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return every asset together with the status from its latest telemetry row."""
    latest_telemetry = _latest_telemetry_subquery(db)

    results = (
        db.query(Asset, latest_telemetry.c.status)
        .outerjoin(
            latest_telemetry,
            (Asset.asset_id == latest_telemetry.c.asset_id) & (latest_telemetry.c.row_number == 1),
        )
        .order_by(Asset.asset_id)
        .all()
    )

    return [
        {
            "asset_id": asset.asset_id,
            "name": asset.name,
            "machine_id": asset.machine_id,
            "criticality": asset.criticality,
            "status": telemetry_status or "unknown",
        }
        for asset, telemetry_status in results
    ]


@router.get("/assets/{asset_id}")
def get_asset_detail(
    asset_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return asset details, its 24-hour telemetry summary, and open alarms."""
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if asset is None:
        raise error_envelope(
            "ASSET_NOT_FOUND",
            f"Asset with ID {asset_id} does not exist",
            404,
        )

    open_alarms = (
        db.query(Alarm)
        .filter(Alarm.asset_id == asset_id, Alarm.resolved.is_(False))
        .order_by(desc(Alarm.ts), desc(Alarm.alarm_id))
        .all()
    )

    day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    summary = (
        db.query(
            func.min(Telemetry.temperature_c).label("min_temp"),
            func.max(Telemetry.temperature_c).label("max_temp"),
            func.avg(Telemetry.temperature_c).label("avg_temp"),
            func.min(Telemetry.pressure_bar).label("min_press"),
            func.max(Telemetry.pressure_bar).label("max_press"),
            func.avg(Telemetry.pressure_bar).label("avg_press"),
        )
        .filter(Telemetry.asset_id == asset_id, Telemetry.ts >= day_ago)
        .first()
    )

    latest_telemetry = (
        db.query(Telemetry)
        .filter(Telemetry.asset_id == asset_id)
        .order_by(desc(Telemetry.ts), desc(Telemetry.id))
        .first()
    )

    return {
        "asset_id": asset.asset_id,
        "name": asset.name,
        "machine_id": asset.machine_id,
        "plant_id": asset.plant_id,
        "line_id": asset.line_id,
        "criticality": asset.criticality,
        "latest_telemetry": (
            {
                "ts": latest_telemetry.ts.isoformat(),
                "temperature_c": _as_float(latest_telemetry.temperature_c),
                "pressure_bar": _as_float(latest_telemetry.pressure_bar),
                "status": latest_telemetry.status or "unknown",
            }
            if latest_telemetry is not None
            else None
        ),
        "summary_24h": {
            "temperature": {
                "min": float(summary.min_temp or 0),
                "max": float(summary.max_temp or 0),
                "avg": float(summary.avg_temp or 0),
            },
            "pressure": {
                "min": float(summary.min_press or 0),
                "max": float(summary.max_press or 0),
                "avg": float(summary.avg_press or 0),
            },
        },
        "open_alarms": [
            {
                "alarm_id": alarm.alarm_id,
                "severity": alarm.severity,
                "code": alarm.code,
                "message": alarm.message,
                "ts": alarm.ts.isoformat(),
            }
            for alarm in open_alarms
        ],
    }


@router.get("/assets/{asset_id}/telemetry")
def get_asset_telemetry(
    asset_id: str,
    range: str = Query("1h", pattern="^(1h|24h|7d)$"),
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return at most 500 telemetry rows from the requested history window."""
    asset_exists = db.query(Asset.asset_id).filter(Asset.asset_id == asset_id).first()
    if asset_exists is None:
        raise error_envelope(
            "ASSET_NOT_FOUND",
            f"Asset with ID {asset_id} does not exist",
            404,
        )

    delta_map = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
    }
    start_time = datetime.now(timezone.utc) - delta_map[range]

    rows = (
        db.query(Telemetry)
        .filter(Telemetry.asset_id == asset_id, Telemetry.ts >= start_time)
        .order_by(desc(Telemetry.ts), desc(Telemetry.id))
        .limit(500)
        .all()
    )

    return [
        {
            "ts": row.ts.isoformat(),
            "metrics": {
                "temperature_c": _as_float(row.temperature_c),
                "pressure_bar": _as_float(row.pressure_bar),
                "vibration_mm_s": _as_float(row.vibration_mm_s),
                "rpm": _as_float(row.rpm),
                "voltage_v": _as_float(row.voltage_v),
                "current_a": _as_float(row.current_a),
                "energy_kwh": _as_float(row.energy_kwh),
            },
            "status": row.status,
        }
        for row in rows
    ]


@router.get("/alerts")
def get_alerts(
    status: str | None = Query(None, pattern="^(critical|warning|resolved)$"),
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return alarms, optionally filtered to open severity or resolved state."""
    query = db.query(Alarm)

    if status == "resolved":
        query = query.filter(Alarm.resolved.is_(True))
    elif status is not None:
        query = query.filter(Alarm.severity == status, Alarm.resolved.is_(False))

    alarms = query.order_by(desc(Alarm.ts), desc(Alarm.alarm_id)).all()
    return [
        {
            "alarm_id": alarm.alarm_id,
            "asset_id": alarm.asset_id,
            "severity": alarm.severity,
            "code": alarm.code,
            "message": alarm.message,
            "ts": alarm.ts.isoformat(),
            "resolved": alarm.resolved,
        }
        for alarm in alarms
    ]


@router.post("/alerts/{alarm_id}/resolve")
def resolve_alarm(
    alarm_id: str,
    user: UserContext = Depends(require_role("admin", "engineer")),
    db: Session = Depends(get_db),
):
    """Resolve an alarm; access is restricted to admin and engineer roles."""
    alarm = db.query(Alarm).filter(Alarm.alarm_id == alarm_id).first()
    if alarm is None:
        raise error_envelope(
            "ALARM_NOT_FOUND",
            f"Alarm code {alarm_id} not found",
            404,
        )

    alarm.resolved = True
    alarm.resolved_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "alarm_id": alarm.alarm_id,
        "resolved": True,
        "resolved_at": alarm.resolved_at.isoformat(),
    }
