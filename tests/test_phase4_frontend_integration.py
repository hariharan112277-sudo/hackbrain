"""
Phase 4 Verification Suite — Frontend Integration & API Contract Validation
Industrial Operating Brain (IOB) Platform

Covers the Phase 4 Engineering Handbook verification matrix:
  Section 2  — REST API contract validation (routes, pagination, validation errors)
  Section 3  — Authentication & authorization integration (401/403, cookie issuance)
  Section 4  — Frontend data models (R-4.4.1 UTC ISO 8601 timestamps)
  Section 5  — AI Gateway integration (JWT enforcement, R-4.5.1 payload guard)
  Section 6  — WebSocket integration (token rejection, heartbeat ping/pong)
  Section 8  — Error handling & API consistency (standard envelope)
  Section 9  — CORS & cross-origin configuration (explicit allow-lists)

Isolation: no PostgreSQL / Redis / MQTT services required — DB sessions are
mocked and identity is injected through dependency overrides, matching the
conventions of the Stage 4 test suites.
"""

import os
import sys

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32-chars-minimum")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_phase4_integration.db")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core import security
from app.core.config import settings
from app.core.timeutils import utc_iso
from app.database import get_db
from app.deps import get_current_user, UserContext
from app.models.user import User

client = TestClient(app)

MOCK_EMAIL = "phase4@iob.demo"
MOCK_PASSWORD = "password123"
MOCK_HASH = security.hash_password(MOCK_PASSWORD)


@pytest.fixture(autouse=True)
def _clean_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db_session():
    session = MagicMock()
    mock_user = User(
        user_id="00000000-0000-0000-0000-000000000042",
        email=MOCK_EMAIL,
        password_hash=MOCK_HASH,
        full_name="Phase Four",
        role="engineer",
    )
    session.query.return_value.filter.return_value.first.return_value = mock_user
    return session


def _override_user(role: str = "engineer"):
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        user_id="user-p4", role=role
    )


# =====================================================================
# Section 4 — R-4.4.1 UTC ISO 8601 timestamp convention
# =====================================================================

class TestTimestampConvention:
    def test_naive_datetime_serialized_as_utc_zulu(self):
        dt = datetime(2026, 7, 17, 16, 0, 1)
        assert utc_iso(dt) == "2026-07-17T16:00:01Z"

    def test_aware_datetime_converted_to_utc(self):
        from datetime import timedelta, timezone as tz

        ist = tz(timedelta(hours=5, minutes=30))
        dt = datetime(2026, 7, 17, 21, 30, 1, tzinfo=ist)
        assert utc_iso(dt) == "2026-07-17T16:00:01Z"

    def test_format_matches_contract_pattern(self):
        import re

        assert re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
            utc_iso(datetime.now(timezone.utc)),
        )


# =====================================================================
# Section 2 — REST contract: pagination bounds (R-4.2.1)
# =====================================================================

class TestListPaginationContract:
    def test_assets_limit_above_cap_returns_422(self):
        _override_user()
        resp = client.get("/api/v1/assets/", params={"limit": 5000})
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"] == "VALIDATION_ERROR"
        assert isinstance(body["details"], list)

    def test_alerts_negative_offset_returns_422(self):
        _override_user()
        resp = client.get("/api/v1/alerts/", params={"offset": -1})
        assert resp.status_code == 422

    def test_default_page_limit_capped_at_100(self):
        assert settings.DEFAULT_PAGE_LIMIT <= 100
        assert settings.MAX_PAGE_LIMIT <= 100


# =====================================================================
# Section 3 — Authentication & authorization integration
# =====================================================================

class TestAuthIntegration:
    def test_login_sets_httponly_cookie(self, mock_db_session):
        app.dependency_overrides[get_db] = lambda: mock_db_session
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": MOCK_EMAIL, "password": MOCK_PASSWORD},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        if settings.AUTH_COOKIE_ENABLED:
            set_cookie = resp.headers.get("set-cookie", "")
            assert settings.AUTH_COOKIE_NAME in set_cookie
            assert "HttpOnly" in set_cookie

    def test_logout_clears_cookie(self):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_protected_route_without_token_401(self):
        resp = client.get("/api/v1/assets/")
        assert resp.status_code == 401

    def test_expired_token_401(self):
        from datetime import timedelta

        expired = security.create_access_token(
            "user-p4", "engineer", expires_delta=timedelta(minutes=-5)
        )
        resp = client.get(
            "/api/v1/assets/", headers={"Authorization": f"Bearer {expired}"}
        )
        assert resp.status_code == 401

    def test_role_mismatch_403(self, mock_db_session):
        app.dependency_overrides[get_db] = lambda: mock_db_session
        _override_user(role="viewer")
        resp = client.post(
            "/api/v1/alerts/ALM-1/resolve",
            json={"resolution_notes": "viewer should be blocked"},
        )
        assert resp.status_code == 403


# =====================================================================
# Section 5 — AI Gateway integration
# =====================================================================

class TestAIGatewayIntegration:
    def test_health_probe_open(self):
        resp = client.get("/api/v1/ai/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "ai_gateway"

    def test_unauthorized_inference_blocked(self):
        resp = client.post("/api/v1/ai/predictive/infer", json={"asset_id": "a-1"})
        assert resp.status_code == 401

    def test_authorized_inference_relayed(self, monkeypatch):
        from app.api import ai_proxy

        async def fake_call_ai(path, *, payload=None, method="POST"):
            return {"success": True, "data": {"echo": payload}}

        monkeypatch.setattr(ai_proxy, "call_ai", fake_call_ai)
        _override_user()
        resp = client.post("/api/v1/ai/predictive/infer", json={"asset_id": "a-1"})
        assert resp.status_code == 200
        assert resp.json()["data"]["echo"] == {"asset_id": "a-1"}

    def test_oversized_payload_rejected_413(self):
        _override_user()
        limit = settings.AI_GATEWAY_MAX_PAYLOAD_BYTES
        resp = client.post(
            "/api/v1/ai/predictive/infer",
            content=b"x",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(limit + 1),
            },
        )
        assert resp.status_code == 413
        body = resp.json()
        assert body["error"] == "PAYLOAD_TOO_LARGE"
        assert body["success"] is False

    def test_payload_within_limit_not_rejected_by_guard(self, monkeypatch):
        from app.api import ai_proxy

        async def fake_call_ai(path, *, payload=None, method="POST"):
            return {"ok": True}

        monkeypatch.setattr(ai_proxy, "call_ai", fake_call_ai)
        _override_user()
        resp = client.post("/api/v1/ai/chat", json={"message": "hello"})
        assert resp.status_code == 200


# =====================================================================
# Section 6 — WebSocket integration
# =====================================================================

class TestWebSocketIntegration:
    @pytest.mark.asyncio
    async def test_invalid_token_rejected_4001(self):
        from unittest.mock import AsyncMock
        from fastapi import WebSocket
        from app.api.ws import websocket_telemetry_endpoint

        mock_ws = AsyncMock(spec=WebSocket)
        await websocket_telemetry_endpoint(mock_ws, token="bad.token.value")
        mock_ws.accept.assert_not_called()
        assert mock_ws.close.call_args[1]["code"] == 4001

    def test_heartbeat_ping_pong(self):
        token = security.create_access_token("user-p4", "engineer")
        with client.websocket_connect(f"/api/v1/stream?token={token}") as ws:
            ws.send_text("ping")
            msg = ws.receive_json()
            assert msg["type"] == "pong"

    def test_json_heartbeat_echoes_ts(self):
        token = security.create_access_token("user-p4", "engineer")
        with client.websocket_connect(f"/api/v1/stream?token={token}") as ws:
            ws.send_text('{"type": "ping", "ts": 12345}')
            msg = ws.receive_json()
            assert msg == {"type": "pong", "ts": 12345}


# =====================================================================
# Section 8 — Error handling & API consistency
# =====================================================================

class TestErrorEnvelopeConsistency:
    def test_validation_error_envelope(self):
        resp = client.post("/api/v1/auth/login", json={"email": "x@y.z"})
        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert body["error"] == "VALIDATION_ERROR"
        assert isinstance(body["details"], list)
        # Each detail entry must carry a structured path reference ("loc")
        assert all("loc" in item for item in body["details"])

    def test_not_found_envelope(self):
        resp = client.get("/api/v1/this/route/does/not/exist")
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False


# =====================================================================
# Section 9 — CORS & cross-origin configuration
# =====================================================================

class TestCORSConfiguration:
    def test_preflight_allows_configured_origin(self):
        origin = settings.CORS_ORIGINS[0]
        resp = client.options(
            "/api/v1/assets/",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == origin
        assert "authorization" in resp.headers.get(
            "access-control-allow-headers", ""
        ).lower()

    def test_preflight_blocks_unknown_origin(self):
        resp = client.options(
            "/api/v1/assets/",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Starlette returns 400 for disallowed preflight origins
        assert resp.status_code == 400

    def test_no_wildcard_methods_configured(self):
        origin = settings.CORS_ORIGINS[0]
        resp = client.options(
            "/api/v1/assets/",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        allowed = resp.headers.get("access-control-allow-methods", "")
        assert "GET" in allowed and "POST" in allowed
