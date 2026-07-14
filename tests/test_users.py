"""
User management API tests.
"""
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.main import create_app

app = create_app()
client = TestClient(app)


def _admin_token():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "SecurePass123!"},
    )
    return response.json()["access_token"]


def test_list_users():
    token = _admin_token()
    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1


def test_create_user():
    token = _admin_token()
    payload = {
        "username": "operator1",
        "email": "operator1@iob.example",
        "password": "SecurePass123",
        "roles": ["operator"],
    }
    response = client.post("/api/v1/users", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "operator1"
    assert body["roles"] == ["operator"]


def test_create_duplicate_user():
    token = _admin_token()
    payload = {
        "username": "operator1",
        "email": "operator1@iob.example",
        "password": "SecurePass123",
        "roles": ["operator"],
    }
    client.post("/api/v1/users", json=payload, headers={"Authorization": f"Bearer {token}"})
    response = client.post("/api/v1/users", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400


def test_get_user():
    token = _admin_token()
    response = client.get("/api/v1/users/u1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == "u1"


def test_update_user():
    token = _admin_token()
    create_resp = client.post(
        "/api/v1/users",
        json={
            "username": "tempuser",
            "email": "tempuser@iob.example",
            "password": "SecurePass123",
            "roles": ["operator"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = create_resp.json()["id"]

    response = client.patch(
        f"/api/v1/users/{user_id}",
        json={"email": "tempuser-updated@iob.example"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "tempuser-updated@iob.example"


def test_delete_user():
    token = _admin_token()
    create_resp = client.post(
        "/api/v1/users",
        json={
            "username": "todelete",
            "email": "todelete@iob.example",
            "password": "SecurePass123",
            "roles": ["operator"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = create_resp.json()["id"]

    response = client.delete(f"/api/v1/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204


def test_list_users_denied_for_operator():
    operator_token = create_access_token(
        data={"sub": "operator", "roles": ["operator"]}
    )
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert response.status_code == 403
