import pytest
from fastapi.testclient import TestClient
from app.main import create_app

app = create_app()
client = TestClient(app)


@pytest.fixture
def auth_header():
    """Returns a valid authorized bearer authorization header."""
    # Obtain a valid token using our mock auth system setup
    response = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "SecurePass123!"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_machines(auth_header):
    response = client.get("/api/v1/machines", headers=auth_header)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["id"] == "m1"


def test_dashboard_summary(auth_header):
    response = client.get("/api/v1/dashboard/summary", headers=auth_header)
    assert response.status_code == 200
    assert response.json()["total_machines"] > 0
