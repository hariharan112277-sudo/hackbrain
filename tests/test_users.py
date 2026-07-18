"""
User management API tests.

Updated to the Phase 5 API contract:
  * Login uses ``email`` + ``password`` against ``/api/v1/auth/login`` (SQLAlchemy session mocked).
  * User CRUD is exposed under ``/api/v1/users`` via ``app/api/users.py``
    (admin-only; returns paginated ``UserListResponse`` / ``UserResponse`` envelopes).
  * For the CRUD tests we override the auth dependency directly (following the
    pattern used across the rest of the test suite) so the tests exercise the
    real endpoints against the stub repository without requiring a pre-seeded
    admin account.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import create_app
from app.core import security
from app.database import get_db
from app.deps import get_current_user, UserContext
from app.models.user import User

app = create_app()
client = TestClient(app)

MOCK_ADMIN_EMAIL = "admin@iob.demo"
MOCK_ADMIN_PASSWORD = "SecurePass123!"
MOCK_ADMIN_HASH = security.hash_password(MOCK_ADMIN_PASSWORD)
MOCK_ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"


def _admin_token():
    """Obtain an admin access token by mocking the DB session."""
    session = MagicMock()
    mock_user = User(
        user_id=uuid.UUID(MOCK_ADMIN_USER_ID),
        email=MOCK_ADMIN_EMAIL,
        password_hash=MOCK_ADMIN_HASH,
        full_name="Local Admin",
        role="admin",
    )
    session.query.return_value.filter.return_value.first.return_value = mock_user
    original = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": MOCK_ADMIN_EMAIL, "password": MOCK_ADMIN_PASSWORD},
        )
        assert response.status_code == 200, response.text
        return response.json()["access_token"]
    finally:
        if original is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_list_users():
    token = _admin_token()
    response = client.get("/api/v1/users", headers=_auth_headers(token))
    assert response.status_code == 200, response.text
    body = response.json()
    # Phase 5 UserListResponse shape
    assert "users" in body
    assert "total" in body
    assert isinstance(body["users"], list)


def test_create_user():
    token = _admin_token()
    payload = {
        "email": "operator1@iob.example",
        "full_name": "Operator One",
        "password": "SecurePass123!!",
        "roles": ["operator"],
    }
    response = client.post("/api/v1/users", json=payload, headers=_auth_headers(token))
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["full_name"] == payload["full_name"]
    assert "id" in body


def test_create_duplicate_user():
    token = _admin_token()
    payload = {
        "email": "operator-dup@iob.example",
        "full_name": "Operator Duplicate",
        "password": "SecurePass123!!",
        "roles": ["operator"],
    }
    client.post("/api/v1/users", json=payload, headers=_auth_headers(token))
    response = client.post("/api/v1/users", json=payload, headers=_auth_headers(token))
    assert response.status_code == 422, response.text


def test_get_user():
    token = _admin_token()
    payload = {
        "email": "getme@iob.example",
        "full_name": "Get Me",
        "password": "SecurePass123!!",
        "roles": ["operator"],
    }
    create_resp = client.post("/api/v1/users", json=payload, headers=_auth_headers(token))
    assert create_resp.status_code == 201, create_resp.text
    user_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/users/{user_id}", headers=_auth_headers(token))
    assert response.status_code == 200, response.text
    assert response.json()["id"] == user_id


def test_update_user():
    token = _admin_token()
    payload = {
        "email": "tempuser@iob.example",
        "full_name": "Temp User",
        "password": "SecurePass123!!",
        "roles": ["operator"],
    }
    create_resp = client.post("/api/v1/users", json=payload, headers=_auth_headers(token))
    assert create_resp.status_code == 201, create_resp.text
    user_id = create_resp.json()["id"]

    response = client.patch(
        f"/api/v1/users/{user_id}",
        json={"email": "tempuser-updated@iob.example"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200, response.text
    assert response.json()["email"] == "tempuser-updated@iob.example"


def test_delete_user():
    token = _admin_token()
    payload = {
        "email": "todelete@iob.example",
        "full_name": "To Delete",
        "password": "SecurePass123!!",
        "roles": ["operator"],
    }
    create_resp = client.post("/api/v1/users", json=payload, headers=_auth_headers(token))
    assert create_resp.status_code == 201, create_resp.text
    user_id = create_resp.json()["id"]

    response = client.delete(f"/api/v1/users/{user_id}", headers=_auth_headers(token))
    assert response.status_code == 204, response.text


def test_list_users_denied_for_operator():
    operator_token = security.create_access_token(
        data={"sub": "operator", "roles": ["operator"]},
    )
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert response.status_code == 403, response.text
