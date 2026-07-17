"""
Authentication Endpoint Test Suites — Track A (Hariharan) — Stage 4 (Testing)
Industrial Operating Brain (IOB) Platform

Validates Stage 2 (Authentication) + Stage 0 (Dependency Layer) integration:
  • POST /api/v1/auth/login  → success path + INVALID_CREDENTIALS failure path
  • POST /api/v1/auth/refresh → valid refresh-token rotation + invalid token rejection
  • GET  /api/v1/auth/me      → authenticated profile retrieval + unauthenticated 401

Isolation:
  All database queries are served from a MagicMock session (no PostgreSQL required).
  Dependency overrides are applied per-test and cleared in teardown to prevent leakage.

Integration wiring (unchanged):
  • app.main.app            — FastAPI instance created via create_app()
  • app.database.get_db     — SQLAlchemy session dependency (mocked)
  • app.core.security       — hash_password, verify_password, JWT token lifecycle
  • app.deps.get_current_user — JWT bearer → UserContext dependency
  • app.models.user.User    — Frozen PostgreSQL ORM (users table)
"""

import os
import sys

# ── Test environment bootstrap ──────────────────────────────────────────────────
# These MUST be set before any app module imports so that Settings()
# validation (SECRET_KEY >= 32 chars, DATABASE_URL required) passes.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32-chars-minimum")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_stage4_auth.db")

import pytest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.core import security
from app.deps import get_current_user, UserContext
from app.models.user import User

client = TestClient(app)

# ── Shared mock identity constants ──────────────────────────────────────────────
MOCK_USER_ID = "00000000-0000-0000-0000-000000000001"
MOCK_EMAIL = "test@iob.demo"
MOCK_PASSWORD = "password123"
MOCK_HASH = security.hash_password(MOCK_PASSWORD)


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture(autouse=True)
def _clean_overrides():
    """Guarantee dependency overrides are cleared after every test."""
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db_session():
    """
    Isolates tests from the PostgreSQL instance by fixing a mocked
    SQLAlchemy session.  User queries return a deterministic mock user
    matching the shared mock credentials above.
    """
    session = MagicMock()
    mock_user = User(
        user_id=MOCK_USER_ID,
        email=MOCK_EMAIL,
        password_hash=MOCK_HASH,
        full_name="Test User",
        role="engineer",
    )
    # Chain: session.query(User).filter(...).first() → mock_user
    session.query.return_value.filter.return_value.first.return_value = mock_user
    return session


# =====================================================================
# POST /api/v1/auth/login — Success Path
# =====================================================================

def test_login_success(mock_db_session):
    """
    Verifies the successful login flow:
      1. Returns HTTP 200
      2. Includes access_token and refresh_token strings
      3. Includes the authenticated user's profile (email matches mock)
      4. Both tokens are non-empty (JWT structural validation deferred to security module tests)
    """
    app.dependency_overrides[get_db] = lambda: mock_db_session

    response = client.post(
        "/api/v1/auth/login",
        json={"email": MOCK_EMAIL, "password": MOCK_PASSWORD},
    )

    assert response.status_code == 200
    data = response.json()

    # Token presence & non-empty
    assert "access_token" in data
    assert "refresh_token" in data
    assert isinstance(data["access_token"], str) and len(data["access_token"]) > 0
    assert isinstance(data["refresh_token"], str) and len(data["refresh_token"]) > 0

    # User profile returned
    assert "user" in data
    assert data["user"]["email"] == MOCK_EMAIL
    assert data["user"]["role"] == "engineer"
    assert data["user"]["user_id"] == MOCK_USER_ID


# =====================================================================
# POST /api/v1/auth/login — Failure Path (invalid credentials)
# =====================================================================

def test_login_invalid_credentials(mock_db_session):
    """
    Verifies the failure path when the supplied password does not match:
      1. Returns HTTP 401
      2. Error body follows the error_envelope schema:
         {"error_code": "INVALID_CREDENTIALS", "message": "..."}
         (FastAPI nests this under the "detail" key in the JSON body)
    """
    app.dependency_overrides[get_db] = lambda: mock_db_session

    response = client.post(
        "/api/v1/auth/login",
        json={"email": MOCK_EMAIL, "password": "wrongpassword"},
    )

    assert response.status_code == 401
    data = response.json()

    # Phase 4 (Section 8 — Error Handling & API Consistency):
    # the global exception handler flattens error_envelope output into the
    # platform-standard structure {"success": false, "error_code": ..., ...}.
    assert data["success"] is False
    assert data["error_code"] == "INVALID_CREDENTIALS"
    assert data["message"] == "Email or password is incorrect"


def test_login_nonexistent_user(mock_db_session):
    """
    Verifies that providing an email not found in the database
    also returns 401 INVALID_CREDENTIALS (no user enumeration).
    """
    # Override query to return None (no user found)
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db_session

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@iob.demo", "password": "anything"},
    )

    assert response.status_code == 401
    data = response.json()
    # Standardized Phase 4 error envelope (no user enumeration)
    assert data["success"] is False
    assert data["error_code"] == "INVALID_CREDENTIALS"


# =====================================================================
# POST /api/v1/auth/refresh — Token Rotation
# =====================================================================

def test_refresh_token_success(mock_db_session):
    """
    Verifies that a valid refresh token yields a new access token:
      1. Obtain tokens via login (mock DB provides valid user)
      2. POST the refresh_token to /api/v1/auth/refresh
      3. Receive a new access_token
    """
    app.dependency_overrides[get_db] = lambda: mock_db_session

    # Step 1: Login to get a valid refresh token
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": MOCK_EMAIL, "password": MOCK_PASSWORD},
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    # Step 2: Exchange refresh token for new access token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str) and len(data["access_token"]) > 0


def test_refresh_token_invalid():
    """
    Verifies that an invalid / malformed refresh token is rejected with 401.
    """
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not.a.valid.jwt.token"},
    )

    assert response.status_code == 401


# =====================================================================
# GET /api/v1/auth/me — Authenticated Profile Retrieval
# =====================================================================

def test_me_endpoint_authenticated(mock_db_session):
    """
    Verifies that an authenticated request to /me returns the correct
    user profile from the database:
      1. Generate a valid JWT via the real create_access_token function
      2. Attach it as a Bearer token
      3. Response body matches the mock user record
    """
    app.dependency_overrides[get_db] = lambda: mock_db_session

    # Generate a real JWT for the mock user (uses the test SECRET_KEY)
    token = security.create_access_token(MOCK_USER_ID, "engineer")

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == MOCK_EMAIL
    assert data["user_id"] == MOCK_USER_ID
    assert data["role"] == "engineer"
    assert data["full_name"] == "Test User"


def test_me_endpoint_unauthenticated():
    """
    Ensures protected endpoints block unauthenticated requests.
    OAuth2PasswordBearer raises HTTP 401 when no Bearer token is present.
    """
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_endpoint_invalid_token():
    """
    Ensures that a malformed / expired JWT is rejected with HTTP 401.
    """
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401
