"""
Integration Tests
Phase 5: End-to-end API integration tests and contract boundary verification.

Updated for the current route/contract map:
  * Auth: POST /api/v1/auth/login (returns access_token + user; no /register).
  * Assets/Alerts/Dashboard/AI use the v1 routes mounted in app.main.create_app().
  * Machine endpoints are consolidated under /api/v1/assets.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core import security
from app.database import get_db
from app.deps import get_current_user, UserContext
from app.models.user import User


# =============================================================================
# Contract Boundary Tests (Member 2 Integration Verification)
# =============================================================================

@pytest.mark.asyncio
async def test_service_integrates_with_repos_correctly():
    """
    Verifies the contract boundaries of Member 2's components.
    This test ensures IndustrialService correctly orchestrates repository calls
    without bypassing the abstraction layer.
    """
    from app.services.industrial_service import IndustrialService

    mock_machine_repo = AsyncMock()
    mock_machine_repo.get_by_id.return_value = {
        "id": "m-100", "name": "Pump-01", "status": "online",
    }

    mock_telemetry_repo = AsyncMock()
    mock_telemetry_repo.get_latest_telemetry.return_value = {
        "metrics": {"vibration": 1.25},
    }

    mock_alarm_repo = AsyncMock()
    mock_metadata_repo = AsyncMock()
    mock_metadata_repo.get_machine_metadata.return_value = {"vendor": "Siemens"}

    service = IndustrialService(
        machine_repo=mock_machine_repo,
        telemetry_repo=mock_telemetry_repo,
        alarm_repo=mock_alarm_repo,
        metadata_repo=mock_metadata_repo,
    )

    result = await service.get_machine_telemetry_flow("m-100")

    assert result["machine_id"] == "m-100"
    assert result["name"] == "Pump-01"
    assert result["metadata"]["vendor"] == "Siemens"
    assert result["telemetry"]["vibration"] == 1.25

    mock_machine_repo.get_by_id.assert_called_once_with("m-100")
    mock_telemetry_repo.get_latest_telemetry.assert_called_once_with("m-100")


# =============================================================================
# Helpers
# =============================================================================

MOCK_EMAIL = "integration@iob.demo"
MOCK_PASSWORD = "SecurePass123!"
MOCK_USER_ID = "00000000-0000-0000-0000-000000000099"


def _mock_db_with_user(role: str = "admin"):
    """Return a MagicMock SQLAlchemy session that resolves to a known user."""
    session = MagicMock()
    mock_user = User(
        user_id=uuid.UUID(MOCK_USER_ID),
        email=MOCK_EMAIL,
        password_hash=security.hash_password(MOCK_PASSWORD),
        full_name="Integration User",
        role=role,
    )
    session.query.return_value.filter.return_value.first.return_value = mock_user
    return session


@pytest.fixture(autouse=True)
def _clean_overrides():
    yield
    app.dependency_overrides.clear()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Full API Integration Tests
# =============================================================================

class TestHealthEndpoints:
    def test_health_check(self):
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_readiness_check(self):
        client = TestClient(app)
        resp = client.get("/ready")
        # May be 200 or 503 depending on DB availability; just assert shape.
        assert resp.status_code in (200, 503)
        assert "status" in resp.json()


class TestAuthentication:
    def test_login_user(self):
        client = TestClient(app)
        app.dependency_overrides[get_db] = lambda: _mock_db_with_user()
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": MOCK_EMAIL, "password": MOCK_PASSWORD},
        )
        assert resp.status_code == 200, resp.text
        assert "access_token" in resp.json()
        assert "refresh_token" in resp.json()

    def test_login_invalid_credentials(self):
        client = TestClient(app)
        app.dependency_overrides[get_db] = lambda: _mock_db_with_user()
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": MOCK_EMAIL, "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_refresh_token(self):
        client = TestClient(app)
        app.dependency_overrides[get_db] = lambda: _mock_db_with_user()
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": MOCK_EMAIL, "password": MOCK_PASSWORD},
        )
        refresh = login_resp.json()["refresh_token"]
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_get_current_user(self):
        client = TestClient(app)
        app.dependency_overrides[get_db] = lambda: _mock_db_with_user()
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": MOCK_EMAIL, "password": MOCK_PASSWORD},
        )
        token = login_resp.json()["access_token"]
        resp = client.get("/api/v1/auth/me", headers=_auth(token))
        assert resp.status_code == 200
        body = resp.json()
        assert "email" in body
        assert "role" in body


class TestAssets:
    """Machine/asset endpoints are consolidated under /api/v1/assets."""

    def test_list_assets_requires_auth(self):
        client = TestClient(app)
        resp = client.get("/api/v1/assets")
        assert resp.status_code == 401

    def test_list_assets_authenticated(self):
        client = TestClient(app)
        empty_db = MagicMock()
        empty_db.query.return_value.outerjoin.return_value.order_by.return_value.all.return_value = []
        app.dependency_overrides[get_db] = lambda: empty_db
        app.dependency_overrides[get_current_user] = lambda: UserContext(
            user_id="user-int", role="engineer",
        )
        resp = client.get("/api/v1/assets")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert body["total_count"] == 0


class TestAlerts:
    def test_list_alarms_requires_auth(self):
        client = TestClient(app)
        resp = client.get("/api/v1/alerts")
        assert resp.status_code == 401


class TestDashboard:
    def test_dashboard_requires_auth(self):
        client = TestClient(app)
        resp = client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401


class TestAIStubs:
    def test_ai_health_open(self):
        client = TestClient(app)
        resp = client.get("/api/v1/ai/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "ai_gateway"

    def test_ai_inference_requires_auth(self):
        client = TestClient(app)
        resp = client.post("/api/v1/ai/predictive/infer", json={"asset_id": "a-1"})
        assert resp.status_code == 401
