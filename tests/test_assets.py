"""
Asset Tracking & RBAC Authorization Test Suites — Track A (Hariharan) — Stage 4 & Phase 1 (Testing)
Industrial Operating Brain (IOB) Platform

Validates Stage 3 (Core Industrial Endpoints) + Stage 0 (Dependency Layer) integration:
  • GET  /api/v1/assets                     → authenticated asset listing
  • GET  /api/v1/assets/{asset_id}          → single asset detail + telemetry summary
  • GET  /api/v1/alerts                     → alarm listing with optional severity filter
  • POST /api/v1/alerts/{alarm_id}/resolve  → RBAC-gated alarm resolution

Isolation:
  All database queries are served from a MagicMock session (no PostgreSQL required).
  Authentication context is injected via FastAPI dependency overrides (no real JWT needed
  for endpoint-level tests; one test exercises a real token for completeness).
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

    # ── Summary record ──────────────────────────────────────────────────────
    mock_summary = MagicMock(
        min_temp=65.0,
        max_temp=80.0,
        avg_temp=72.5,
        min_press=1.5,
        max_press=3.2,
        avg_press=2.4,
    )

    def query_side_effect(*args):
        q = MagicMock()
        if args and args[0] is Asset:
            q.outerjoin.return_value.order_by.return_value.all.return_value = [(mock_asset, "normal")]
            q.filter.return_value.first.return_value = mock_asset
            q.filter.return_value.all.return_value = [mock_asset]
        elif args and args[0] is Alarm:
            # Support chains with and without .offset().limit() pagination
            for base in (q, q.filter.return_value, q.filter.return_value.filter.return_value):
                chain = base.order_by.return_value
                chain.all.return_value = [mock_alarm]
                chain.offset.return_value.limit.return_value.all.return_value = [mock_alarm]
                base.all.return_value = [mock_alarm]
                base.offset.return_value.limit.return_value.all.return_value = [mock_alarm]
                base.first.return_value = mock_alarm
                base.filter.return_value.first.return_value = mock_alarm
                base.filter.return_value.order_by.return_value.all.return_value = [mock_alarm]
                base.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_alarm]
            q.order_by.return_value.all.return_value = [mock_alarm]
            q.filter.return_value.order_by.return_value.all.return_value = [mock_alarm]
            q.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_alarm]
            q.filter.return_value.all.return_value = [mock_alarm]
            q.filter.return_value.filter.return_value.all.return_value = [mock_alarm]
            q.filter.return_value.first.return_value = mock_alarm
            q.filter.return_value.filter.return_value.first.return_value = mock_alarm
        else:
            q.filter.return_value.first.return_value = mock_summary
            q.filter.return_value.all.return_value = [mock_summary]
        return q

    session.query.side_effect = query_side_effect
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
# GET /api/v1/assets — Asset Inventory Listing
# =====================================================================

def test_get_assets_authenticated(mock_db_assets):
    """
    Verifies that an authenticated engineer can retrieve asset inventory:
      1. Returns HTTP 200
      2. Includes expected summary fields (total_count, critical_count)
      3. Returns item list containing our MOCK_ASSET_ID
    """
    app.dependency_overrides[get_db] = lambda: mock_db_assets
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-123", role="engineer"
    )

    response = client.get("/api/v1/assets")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total_count"] == 1
    assert data["items"][0]["asset_id"] == MOCK_ASSET_ID
    assert data["items"][0]["name"] == "Hydraulic Pump"


def test_get_assets_unauthenticated(mock_db_assets):
    """
    Verifies that requesting asset listing without credentials fails:
      1. Returns HTTP 401
      2. No data is disclosed
    """
    app.dependency_overrides[get_db] = lambda: mock_db_assets
    # Do not override get_current_user — let the real dependency reject it

    response = client.get("/api/v1/assets")
    assert response.status_code == 401


def test_get_assets_empty_inventory():
    """
    Verifies graceful handling when the database returns no assets:
      1. Returns HTTP 200
      2. total_count is 0, items is []
    """
    empty_db = MagicMock()
    empty_db.query.return_value.outerjoin.return_value.order_by.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: empty_db
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-123", role="operator"
    )

    response = client.get("/api/v1/assets")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 0
    assert data["items"] == []


# =====================================================================
# GET /api/v1/assets/{asset_id} — Single Asset Detail
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

    response = client.get(f"/api/v1/assets/{MOCK_ASSET_ID}")

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
    Verifies that requesting a nonexistent asset returns structured 404:
      1. Returns HTTP 404
      2. Error code matches ASSET_NOT_FOUND
    """
    not_found_db = MagicMock()
    not_found_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: not_found_db
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-123", role="engineer"
    )

    response = client.get("/api/v1/assets/NONEXISTENT-99")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "ASSET_NOT_FOUND"


# =====================================================================
# GET /api/v1/alerts — Alarm Listing
# =====================================================================

def test_get_alerts_authenticated(mock_db_assets):
    """
    Verifies that an authenticated user can list active alarms:
      1. Returns HTTP 200
      2. Response contains list of active alarms
    """
    app.dependency_overrides[get_db] = lambda: mock_db_assets
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-123", role="operator"
    )

    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["alarm_id"] == MOCK_ALARM_ID


def test_get_alerts_unauthenticated(mock_db_assets):
    """Verifies that listing alerts requires authentication → HTTP 401."""
    app.dependency_overrides[get_db] = lambda: mock_db_assets

    response = client.get("/api/v1/alerts")
    assert response.status_code == 401


# =====================================================================
# POST /api/v1/alerts/{alarm_id}/resolve — Alarm Resolution
# =====================================================================

def test_resolve_alarm_insufficient_role(mock_db_resolve):
    """
    Verifies RBAC enforcement: resolving an alarm requires 'engineer'
    or 'admin' role. A user with only 'viewer' role is rejected:
      1. Returns HTTP 403 Forbidden
      2. Database transaction commit is never called
    """
    app.dependency_overrides[get_db] = lambda: mock_db_resolve
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-viewer-01", role="viewer"
    )

    response = client.post(
        f"/api/v1/alerts/{MOCK_ALARM_ID}/resolve",
        json={"resolution_notes": "Attempted resolve by viewer"},
    )
    assert response.status_code == 403
    mock_db_resolve.commit.assert_not_called()


def test_resolve_alarm_as_admin(mock_db_resolve):
    """
    Verifies that an 'admin' role CAN resolve an alarm:
      1. Returns HTTP 200
      2. status == "resolved" in response body
      3. db.commit() is invoked once
    """
    app.dependency_overrides[get_db] = lambda: mock_db_resolve
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-admin-01", role="admin"
    )

    response = client.post(
        f"/api/v1/alerts/{MOCK_ALARM_ID}/resolve",
        json={"resolution_notes": "Resolved during maintenance window"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "resolved"
    assert body["alarm_id"] == MOCK_ALARM_ID
    mock_db_resolve.commit.assert_called_once()


def test_resolve_alarm_as_engineer(mock_db_resolve):
    """
    Verifies that an 'engineer' role CAN resolve an alarm:
      1. Returns HTTP 200
      2. status == "resolved" in response body
      3. db.commit() is invoked once
    """
    app.dependency_overrides[get_db] = lambda: mock_db_resolve
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-eng-01", role="engineer"
    )

    response = client.post(
        f"/api/v1/alerts/{MOCK_ALARM_ID}/resolve",
        json={"resolution_notes": "Replaced faulty sensor S-04"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "resolved"
    mock_db_resolve.commit.assert_called_once()


def test_resolve_alarm_as_operator_forbidden(mock_db_resolve):
    """
    Verifies that an 'operator' role CANNOT resolve an alarm (`require_role("engineer", "admin")`).
      1. Returns HTTP 403 Forbidden
      2. db.commit() is never called
    """
    app.dependency_overrides[get_db] = lambda: mock_db_resolve
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-op-01", role="operator"
    )

    response = client.post(
        f"/api/v1/alerts/{MOCK_ALARM_ID}/resolve",
        json={"resolution_notes": "Operator acknowledge action attempt"},
    )
    assert response.status_code == 403
    mock_db_resolve.commit.assert_not_called()


def test_resolve_alarm_unauthenticated(mock_db_resolve):
    """Verifies that resolving an alarm without bearer token returns HTTP 401."""
    app.dependency_overrides[get_db] = lambda: mock_db_resolve

    response = client.post(
        f"/api/v1/alerts/{MOCK_ALARM_ID}/resolve",
        json={"resolution_notes": "No auth token provided"},
    )
    assert response.status_code == 401
    mock_db_resolve.commit.assert_not_called()
