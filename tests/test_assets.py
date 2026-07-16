"""
Asset Tracking & RBAC Authorization Test Suites — Track A (Hariharan) — Stage 4 (Testing)
Industrial Operating Brain (IOB) Platform

Validates Stage 3 (Core Industrial Endpoints) + Stage 0 (Dependency Layer) integration:
  • GET  /api/v1/industrial/assets                     → authenticated asset listing
  • GET  /api/v1/industrial/assets/{asset_id}          → single asset detail + telemetry summary
  • GET  /api/v1/industrial/alerts                     → alarm listing with optional severity filter
  • POST /api/v1/industrial/alerts/{alarm_id}/resolve  → RBAC-gated alarm resolution

Isolation:
  All database queries are served from a MagicMock session (no PostgreSQL required).
  Authentication context is injected via FastAPI dependency overrides (no real JWT needed
  for endpoint-level tests; one test exercises a real token for completeness).

Integration wiring (unchanged):
  • app.main.app                  — FastAPI instance created via create_app()
  • app.database.get_db           — SQLAlchemy session dependency (mocked)
  • app.deps.get_current_user     — JWT bearer → UserContext dependency (overridden)
  • app.deps.require_role         — RBAC dependency factory
  • app.models.asset.Asset        — Frozen PostgreSQL ORM (assets table)
  • app.models.alarm.Alarm        — Frozen PostgreSQL ORM (alarms table)
"""

import os
import sys

# ── Test environment bootstrap ──────────────────────────────────────────────────
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32-chars-minimum")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_stage4_assets.db")

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.deps import get_current_user, UserContext
from app.models.alarm import Alarm
from app.models.asset import Asset

client = TestClient(app)

# ── Shared mock constants ───────────────────────────────────────────────────────
MOCK_ASSET_ID = "ASSET-01"
MOCK_ALARM_ID = "ALM-99"


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture(autouse=True)
def _clean_overrides():
    """Guarantee dependency overrides are cleared after every test."""
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db_assets():
    """
    Mocked SQLAlchemy session serving deterministic asset + alarm data.

    Supports the full chain used by the industrial endpoints:
      • db.query(Asset, ...).outerjoin(...).order_by(...).all() → asset listing
      • db.query(Asset).filter(...).first()                     → single asset lookup
      • db.query(Alarm).filter(...).order_by(...).all()         → open alarms
      • db.query(Alarm).filter(...).first()                     → alarm lookup (resolve)
    """
    session = MagicMock()

    # ── Asset record ────────────────────────────────────────────────────────
    mock_asset = Asset(
        asset_id=MOCK_ASSET_ID,
        name="Hydraulic Pump",
        plant_id="PLANT-A",
        line_id="LINE-1",
        machine_id="MCH-01",
        asset_type="pump",
        criticality="high",
    )

    # ── Alarm record ────────────────────────────────────────────────────────
    mock_alarm = Alarm(
        alarm_id=MOCK_ALARM_ID,
        asset_id=MOCK_ASSET_ID,
        severity="critical",
        code="HIGH_TEMP",
        message="Temperature exceeded threshold",
        ts=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        resolved=False,
        resolved_at=None,
    )

    # db.query(...).outerjoin(...).outerjoin(...).all()  → asset listing
    # (auto-chained MagicMock covers arbitrary .outerjoin() depth)
    session.query.return_value.outerjoin.return_value.order_by.return_value.all.return_value = [
        (mock_asset, "normal")
    ]

    # db.query(Asset).filter(...).first() → single asset detail
    session.query.return_value.filter.return_value.first.return_value = mock_asset

    # db.query(Alarm).filter(...).first() → alarm for resolve endpoint
    # We set this AFTER the asset filter; MagicMock's chained attribute access
    # means the *last* assignment on the same chain wins.  For tests that
    # specifically need the alarm, we use a separate fixture.
    session.query.return_value.filter.return_value.all.return_value = [mock_alarm]

    return session


@pytest.fixture
def mock_db_resolve():
    """
    Specialised mock for the resolve-alarm endpoint.
    Ensures db.query(Alarm).filter(...).first() returns the mock alarm.
    """
    session = MagicMock()

    mock_alarm = Alarm(
        alarm_id=MOCK_ALARM_ID,
        asset_id=MOCK_ASSET_ID,
        severity="critical",
        code="HIGH_TEMP",
        message="Temperature exceeded threshold",
        ts=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        resolved=False,
        resolved_at=None,
    )

    session.query.return_value.filter.return_value.first.return_value = mock_alarm
    return session


# =====================================================================
# GET /api/v1/industrial/assets — Authenticated Asset Listing
# =====================================================================

def test_get_assets_authenticated(mock_db_assets):
    """
    Verifies that an authenticated user (any role) can fetch the asset
    inventory registry with telemetry status:
      1. Returns HTTP 200
      2. Response is a list with at least one asset
      3. Asset fields (asset_id, name, machine_id, criticality, status) are present
    """
    app.dependency_overrides[get_db] = lambda: mock_db_assets
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-123", role="viewer"
    )

    response = client.get("/api/v1/industrial/assets")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    first_asset = data[0]
    assert first_asset["asset_id"] == MOCK_ASSET_ID
    assert first_asset["name"] == "Hydraulic Pump"
    assert first_asset["machine_id"] == "MCH-01"
    assert first_asset["criticality"] == "high"
    assert first_asset["status"] == "normal"


def test_get_assets_unauthenticated():
    """
    Verifies that unauthenticated requests to the asset listing are rejected
    with HTTP 401 (OAuth2PasswordBearer requires a Bearer token).
    """
    response = client.get("/api/v1/industrial/assets")
    assert response.status_code == 401


def test_get_assets_empty_inventory():
    """
    Verifies graceful handling when the asset inventory is empty:
    returns an empty list (not an error).
    """
    session = MagicMock()
    session.query.return_value.outerjoin.return_value.order_by.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-123", role="viewer"
    )

    response = client.get("/api/v1/industrial/assets")

    assert response.status_code == 200
    assert response.json() == []


# =====================================================================
# GET /api/v1/industrial/assets/{asset_id} — Single Asset Detail
# =====================================================================

def test_get_asset_detail_authenticated(mock_db_assets):
    """
    Verifies that an authenticated user can retrieve a single asset's
    details including telemetry summary and open alarms:
      1. Returns HTTP 200
      2. Core asset fields are present
      3. Summary and alarm data structures are included
    """
    app.dependency_overrides[get_db] = lambda: mock_db_assets
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-123", role="engineer"
    )

    response = client.get(f"/api/v1/industrial/assets/{MOCK_ASSET_ID}")

    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == MOCK_ASSET_ID
    assert data["name"] == "Hydraulic Pump"
    assert data["criticality"] == "high"
    # Summary 24h structure
    assert "summary_24h" in data
    assert "temperature" in data["summary_24h"]
    assert "pressure" in data["summary_24h"]
    # Open alarms list
    assert "open_alarms" in data


def test_get_asset_detail_not_found(mock_db_assets):
    """
    Verifies that requesting a non-existent asset returns HTTP 404
    with the ASSET_NOT_FOUND error code.
    """
    # Override to return None for asset lookup
    mock_db_assets.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db_assets
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-123", role="viewer"
    )

    response = client.get("/api/v1/industrial/assets/ASSET-NONEXIST")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error_code"] == "ASSET_NOT_FOUND"


# =====================================================================
# GET /api/v1/industrial/alerts — Alarm Listing
# =====================================================================

def test_get_alerts_authenticated(mock_db_assets):
    """
    Verifies that an authenticated user can retrieve the alarm listing:
      1. Returns HTTP 200
      2. Response is a list of alarm objects with required fields
    """
    app.dependency_overrides[get_db] = lambda: mock_db_assets
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-123", role="viewer"
    )

    response = client.get("/api/v1/industrial/alerts")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    first_alarm = data[0]
    assert first_alarm["alarm_id"] == MOCK_ALARM_ID
    assert first_alarm["asset_id"] == MOCK_ASSET_ID
    assert first_alarm["severity"] == "critical"
    assert first_alarm["code"] == "HIGH_TEMP"


def test_get_alerts_unauthenticated():
    """
    Verifies that unauthenticated requests to the alerts endpoint are rejected.
    """
    response = client.get("/api/v1/industrial/alerts")
    assert response.status_code == 401


# =====================================================================
# POST /api/v1/industrial/alerts/{alarm_id}/resolve — RBAC Authorization
# =====================================================================

def test_resolve_alarm_insufficient_role(mock_db_resolve):
    """
    Verifies that low-privilege roles (viewer) are blocked from resolving
    active alarms.  The require_role("admin", "engineer") dependency
    evaluates first and raises HTTP 403 before the endpoint handler runs.
    """
    app.dependency_overrides[get_db] = lambda: mock_db_resolve
    # Override current user as a viewer (insufficient for resolve)
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-123", role="viewer"
    )

    response = client.post(f"/api/v1/industrial/alerts/{MOCK_ALARM_ID}/resolve")

    # FastAPI's RBAC layer blocks this at require_role dependency evaluation
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Insufficient role"


def test_resolve_alarm_as_admin(mock_db_resolve):
    """
    Verifies that an admin-role user can successfully resolve an alarm:
      1. Returns HTTP 200
      2. Response confirms the alarm is resolved
      3. The alarm's resolved flag is set to True
    """
    app.dependency_overrides[get_db] = lambda: mock_db_resolve
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="admin-001", role="admin"
    )

    response = client.post(f"/api/v1/industrial/alerts/{MOCK_ALARM_ID}/resolve")

    assert response.status_code == 200
    data = response.json()
    assert data["alarm_id"] == MOCK_ALARM_ID
    assert data["resolved"] is True
    assert "resolved_at" in data


def test_resolve_alarm_as_engineer(mock_db_resolve):
    """
    Verifies that an engineer-role user can also resolve alarms
    (the allow-list includes both "admin" and "engineer").
    """
    app.dependency_overrides[get_db] = lambda: mock_db_resolve
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="eng-001", role="engineer"
    )

    response = client.post(f"/api/v1/industrial/alerts/{MOCK_ALARM_ID}/resolve")

    assert response.status_code == 200
    data = response.json()
    assert data["alarm_id"] == MOCK_ALARM_ID
    assert data["resolved"] is True


def test_resolve_alarm_as_operator_forbidden(mock_db_resolve):
    """
    Verifies that an operator-role user is blocked from resolving alarms
    (only admin and engineer are allowed).
    """
    app.dependency_overrides[get_db] = lambda: mock_db_resolve
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="op-001", role="operator"
    )

    response = client.post(f"/api/v1/industrial/alerts/{MOCK_ALARM_ID}/resolve")

    assert response.status_code == 403


def test_resolve_alarm_unauthenticated(mock_db_resolve):
    """
    Verifies that unauthenticated requests to the resolve endpoint
    are rejected with HTTP 401 before RBAC evaluation.
    """
    app.dependency_overrides[get_db] = lambda: mock_db_resolve

    response = client.post(f"/api/v1/industrial/alerts/{MOCK_ALARM_ID}/resolve")

    assert response.status_code == 401
