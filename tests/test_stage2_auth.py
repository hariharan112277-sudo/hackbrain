"""
Stage 2 Verification Tests — Track A (Hariharan) — Authentication

Covers Checkpoint 2 without requiring a live PostgreSQL instance:
  * bcrypt hash / verify
  * access + refresh JWT lifecycle
  * decode_token success + 401 failure paths
  * /login, /refresh, /me endpoint behaviour via FastAPI TestClient
  * backward-compat surface for Phase-5 / Stage-0 callers
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from jose import jwt

sys.path.insert(0, ".")

# Provide env so Settings can construct during imports
import os

os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-for-stage2-auth-at-least-32-chars",
)
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_stage2.db")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from app.core import security
from app.core.config import settings
from app.core.errors import error_envelope
from app.core.exceptions import AuthenticationError
from app.deps import UserContext, get_current_user
from app.models.schemas import LoginRequest, RefreshRequest
from app.models.user import User


# =====================================================================
# 1. Password hashing
# =====================================================================

class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = security.hash_password("admin123")
        assert hashed != "admin123"
        assert hashed.startswith("$2b$")
        assert security.verify_password("admin123", hashed) is True
        assert security.verify_password("wrong", hashed) is False

    def test_get_password_hash_alias(self):
        h = security.get_password_hash("engineer123")
        assert security.verify_password("engineer123", h)


# =====================================================================
# 2. Token lifecycle
# =====================================================================

class TestTokenLifecycle:
    def test_create_access_token_stage2(self):
        token = security.create_access_token("user-1", "admin")
        payload = security.decode_token(token)
        assert payload["sub"] == "user-1"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token_stage2(self):
        token = security.create_refresh_token("user-1", role="admin")
        payload = security.decode_token(token)
        assert payload["sub"] == "user-1"
        assert payload["type"] == "refresh"
        assert payload["role"] == "admin"

    def test_create_access_token_phase5_dict(self):
        token = security.create_access_token(
            {"sub": "u-99", "email": "a@b.com", "roles": ["operator"]},
            expires_delta=timedelta(minutes=15),
        )
        payload = security.verify_token(token)
        assert payload["sub"] == "u-99"
        assert payload["type"] == "access"
        assert payload["role"] == "operator"  # normalised from roles list

    def test_create_refresh_token_phase5_dict(self):
        token = security.create_refresh_token(
            {"sub": "u-99", "roles": ["viewer"]},
        )
        payload = security.verify_token(token)
        assert payload["type"] == "refresh"
        assert payload["role"] == "viewer"

    def test_decode_invalid_raises_401(self):
        with pytest.raises(HTTPException) as ei:
            security.decode_token("not.a.valid.jwt")
        assert ei.value.status_code == 401
        assert ei.value.headers.get("WWW-Authenticate") == "Bearer"

    def test_decode_expired_raises_401(self):
        expire = datetime.now(timezone.utc) - timedelta(hours=1)
        token = jwt.encode(
            {"sub": "x", "role": "admin", "exp": expire},
            settings.SECRET_KEY,
            algorithm="HS256",
        )
        with pytest.raises(HTTPException) as ei:
            security.decode_token(token)
        assert ei.value.status_code == 401

    def test_verify_token_raises_auth_error(self):
        with pytest.raises(AuthenticationError):
            security.verify_token("garbage.token.value")


# =====================================================================
# 3. error_envelope
# =====================================================================

class TestErrorEnvelope:
    def test_raises_structured_401(self):
        exc = error_envelope("INVALID_CREDENTIALS", "bad creds", 401)
        assert isinstance(exc, HTTPException)
        assert exc.status_code == 401
        assert exc.detail["error_code"] == "INVALID_CREDENTIALS"
        assert exc.detail["message"] == "bad creds"
        assert exc.headers.get("WWW-Authenticate") == "Bearer"


# =====================================================================
# 4. Endpoint tests (in-memory mock DB)
# =====================================================================

def _make_user(
    email: str = "admin@iob.demo",
    password: str = "admin123",
    role: str = "admin",
    full_name: str = "Demo Admin",
) -> User:
    u = MagicMock(spec=User)
    u.user_id = uuid.uuid4()
    u.email = email
    u.password_hash = security.hash_password(password)
    u.full_name = full_name
    u.role = role
    return u


@pytest.fixture()
def auth_client() -> Generator[TestClient, None, None]:
    """
    Minimal FastAPI app mounting only the Stage-2 auth router,
    with get_db overridden to an in-memory user store.
    """
    from app.api.auth import router as auth_router
    from app.database import get_db

    demo_user = _make_user()
    store = {demo_user.email: demo_user}

    def _fake_get_db():
        session = MagicMock()

        def _query(model):
            q = MagicMock()

            def _filter(*args, **kwargs):
                # Support filter by email or user_id via the expression left side
                f = MagicMock()

                def _first():
                    # Inspect call stack heuristically: login uses email, me uses user_id
                    # We re-bind based on the last filter expression string
                    expr = str(args[0]) if args else ""
                    if "email" in expr.lower() or "@" in expr:
                        # body.email comparison — pull from store by scanning
                        for u in store.values():
                            # The SQLAlchemy BinaryExpression string contains the bound value poorly;
                            # instead, expose a helper via session._lookup_email set by side_effect
                            pass
                    return None

                f.first = _first
                return f

            q.filter = _filter
            return q

        # More robust: implement filter via custom side_effect capturing values
        class _Query:
            def __init__(self):
                self._email = None
                self._uid = None

            def filter(self, *args, **kwargs):
                # Extract right-hand side of BinaryExpression when available
                for a in args:
                    try:
                        # SQLAlchemy BinaryExpression: .right.value or .right
                        right = getattr(a, "right", None)
                        left = getattr(a, "left", None)
                        val = getattr(right, "value", right)
                        col = str(getattr(left, "key", left) or left)
                        if "email" in col:
                            self._email = val
                        elif "user_id" in col:
                            self._uid = val
                    except Exception:
                        pass
                return self

            def first(self):
                if self._email is not None:
                    return store.get(self._email)
                if self._uid is not None:
                    for u in store.values():
                        if str(u.user_id) == str(self._uid):
                            return u
                return None

        session.query = lambda model: _Query()
        try:
            yield session
        finally:
            pass

    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1/auth")
    app.dependency_overrides[get_db] = _fake_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


class TestAuthEndpoints:
    def test_login_success(self, auth_client: TestClient):
        resp = auth_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@iob.demo", "password": "admin123"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["user"]["email"] == "admin@iob.demo"
        assert body["user"]["role"] == "admin"
        # Tokens must be decodable
        access_payload = security.decode_token(body["access_token"])
        assert access_payload["role"] == "admin"
        assert access_payload["type"] == "access"
        refresh_payload = security.decode_token(body["refresh_token"])
        assert refresh_payload["type"] == "refresh"

    def test_login_bad_password(self, auth_client: TestClient):
        resp = auth_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@iob.demo", "password": "wrong"},
        )
        assert resp.status_code == 401
        detail = resp.json()["detail"]
        assert detail["error_code"] == "INVALID_CREDENTIALS"

    def test_login_unknown_user(self, auth_client: TestClient):
        resp = auth_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@iob.demo", "password": "admin123"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["error_code"] == "INVALID_CREDENTIALS"

    def test_refresh_success(self, auth_client: TestClient):
        login = auth_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@iob.demo", "password": "admin123"},
        ).json()
        resp = auth_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login["refresh_token"]},
        )
        assert resp.status_code == 200, resp.text
        assert "access_token" in resp.json()
        payload = security.decode_token(resp.json()["access_token"])
        assert payload["type"] == "access"
        assert payload["role"] == "admin"

    def test_refresh_rejects_access_token(self, auth_client: TestClient):
        login = auth_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@iob.demo", "password": "admin123"},
        ).json()
        resp = auth_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login["access_token"]},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["error_code"] == "INVALID_TOKEN"

    def test_me_authenticated(self, auth_client: TestClient):
        login = auth_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@iob.demo", "password": "admin123"},
        ).json()
        resp = auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login['access_token']}"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["email"] == "admin@iob.demo"
        assert body["role"] == "admin"
        assert body["full_name"] == "Demo Admin"

    def test_me_unauthenticated(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# =====================================================================
# 5. Schemas exist
# =====================================================================

class TestSchemas:
    def test_login_request(self):
        body = LoginRequest(email="admin@iob.demo", password="admin123")
        assert body.email == "admin@iob.demo"

    def test_refresh_request(self):
        body = RefreshRequest(refresh_token="abc.def.ghi")
        assert body.refresh_token.startswith("abc")


# =====================================================================
# 6. Stage-0 coexistence
# =====================================================================

class TestStage0Coexistence:
    def test_deps_get_current_user_accepts_stage2_token(self):
        token = security.create_access_token("uid-42", "engineer")
        ctx = get_current_user(token=token)
        assert isinstance(ctx, UserContext)
        assert ctx.user_id == "uid-42"
        assert ctx.role == "engineer"

    def test_security_and_deps_get_current_user_differ(self):
        from app.core.security import get_current_user as sec_gcu
        from app.deps import get_current_user as deps_gcu
        assert sec_gcu is not deps_gcu
