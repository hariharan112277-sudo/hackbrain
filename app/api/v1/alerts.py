"""Canonical alert operations API."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import UserContext, get_current_user, require_role
from app.models.alarm import Alarm
from app.core.timeutils import utc_iso

router = APIRouter()

@router.get("")
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
            "ts": utc_iso(alarm.ts),
            "resolved": alarm.resolved,
        }
        for alarm in alarms
    ]


@router.post("/{alarm_id}/resolve")
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
        "status": "resolved",
        "resolved": True,
        "resolved_at": utc_iso(alarm.resolved_at),
    }
