"""
Authentication API tests.
"""
from fastapi.testclient import TestClient
from app.main import create_app

app = create_app()
client = TestClient(app)


def test_login_success():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "SecurePass123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_failure():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrongpass"},
    )
    assert response.status_code == 401


def test_me_endpoint():
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "SecurePass123!"},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/users/u1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_me_without_token():
    response = client.get("/api/v1/users/u1")
    assert response.status_code == 401


def test_refresh_token():
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "SecurePass123!"},
    )
    refresh_token = login.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_logout():
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "SecurePass123!"},
    )
    token = login.json()["access_token"]
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204
