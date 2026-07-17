"""
UTC Timestamp Utilities — Phase 4 (R-4.4.1)
Industrial Operating Brain (IOB) Platform

Enforces the strict UTC ISO 8601 formatting convention
(`YYYY-MM-DDTHH:mm:ssZ`) for all system timestamps so frontend
dashboards never receive ambiguous or zone-less datetimes.

Reference: Phase 4 Engineering Handbook, Section 4 (Frontend Data Models),
Recommendation R-4.4.1.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Return the current time as an aware UTC datetime."""
    return datetime.now(timezone.utc)


def utc_iso(dt: Optional[datetime] = None) -> str:
    """Serialize a datetime as strict UTC ISO 8601 (``YYYY-MM-DDTHH:mm:ssZ``).

    Naive datetimes are assumed to already be UTC (matching the storage
    convention used by the telemetry pipeline). Aware datetimes are
    converted to UTC before formatting. Sub-second precision is dropped
    to keep the wire format stable for frontend consumers.
    """
    if dt is None:
        dt = utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = ["utc_now", "utc_iso"]
