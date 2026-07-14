"""
Integration Tests
Phase 5: End-to-end API integration tests and contract boundary verification.
"""

import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timedelta


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

    # Setup Async Mock Contracts to simulate Member 2 repository classes
    mock_machine_repo = AsyncMock()
    mock_machine_repo.get_by_id.return_value = {"id": "m-100", "name": "Pump-01", "status": "online"}

    mock_telemetry_repo = AsyncMock()
    mock_telemetry_repo.get_latest_telemetry.return_value = {"metrics": {"vibration": 1.25}}

    mock_alarm_repo = AsyncMock()
    mock_metadata_repo = AsyncMock()
    mock_metadata_repo.get_machine_metadata.return_value = {"vendor": "Siemens"}

    service = IndustrialService(
        machine_repo=mock_machine_repo,
        telemetry_repo=mock_telemetry_repo,
        alarm_repo=mock_alarm_repo,
        metadata_repo=mock_metadata_repo
    )

    # Execute and Verify Orchestration flow
    result = await service.get_machine_telemetry_flow("m-100")

    assert result["machine_id"] == "m-100"
    assert result["name"] == "Pump-01"
    assert result["metadata"]["vendor"] == "Siemens"
    assert result["telemetry"]["vibration"] == 1.25

    # Verify boundaries: no direct repository bypasses or file writes
    mock_machine_repo.get_by_id.assert_called_once_with("m-100")
    mock_telemetry_repo.get_latest_telemetry.assert_called_once_with("m-100")


# =============================================================================
# Full API Integration Tests
# =============================================================================

class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test basic health check."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_readiness_check(self, async_client: AsyncClient):
        """Test readiness check."""
        response = await async_client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"


class TestAuthentication:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_user(self, async_client: AsyncClient):
        """Test user registration."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
                "role": "operator",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_user(self, async_client: AsyncClient):
        """Test user login."""
        # First register
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "loginuser@example.com",
                "password": "SecurePass123!",
                "full_name": "Login User",
            },
        )

        # Then login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "loginuser@example.com",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """Test login with invalid credentials."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self, async_client: AsyncClient):
        """Test token refresh."""
        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "refreshuser@example.com",
                "password": "SecurePass123!",
                "full_name": "Refresh User",
            },
        )

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "refreshuser@example.com",
                "password": "SecurePass123!",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_get_current_user(self, async_client: AsyncClient):
        """Test getting current user info."""
        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "meuser@example.com",
                "password": "SecurePass123!",
                "full_name": "Me User",
            },
        )

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "meuser@example.com",
                "password": "SecurePass123!",
            },
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data


class TestMachines:
    """Test machine endpoints."""

    @pytest.mark.asyncio
    async def test_list_machines(self, async_client: AsyncClient):
        """Test listing machines."""
        # Login first
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )
        token = login_response.json()["access_token"]

        response = await async_client.get(
            "/api/v1/industrial/machines",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "machines" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_create_machine(self, async_client: AsyncClient):
        """Test creating a machine."""
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )
        token = login_response.json()["access_token"]

        response = await async_client.post(
            "/api/v1/industrial/machines",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Machine",
                "serial_number": "TM-TEST-001",
                "model": "TM-100",
                "manufacturer": "Test Corp",
                "location": "Factory A",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Machine"
        assert data["serial_number"] == "TM-TEST-001"


class TestTelemetry:
    """Test telemetry endpoints."""

    @pytest.mark.asyncio
    async def test_get_latest_telemetry(self, async_client: AsyncClient):
        """Test getting latest telemetry."""
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )
        token = login_response.json()["access_token"]

        # First create a machine
        machine_response = await async_client.post(
            "/api/v1/industrial/machines",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Telemetry Machine",
                "serial_number": "TM-TELE-001",
                "model": "TM-200",
            },
        )
        machine_id = machine_response.json()["id"]

        response = await async_client.get(
            f"/api/v1/industrial/machines/{machine_id}/telemetry",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "machine_id" in data
        assert "metrics" in data

    @pytest.mark.asyncio
    async def test_get_telemetry_flow(self, async_client: AsyncClient):
        """Test getting machine telemetry flow."""
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )
        token = login_response.json()["access_token"]

        machine_response = await async_client.post(
            "/api/v1/industrial/machines",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Flow Machine",
                "serial_number": "TM-FLOW-001",
            },
        )
        machine_id = machine_response.json()["id"]

        response = await async_client.get(
            f"/api/v1/industrial/machines/{machine_id}/telemetry/flow",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "machine_id" in data
        assert "telemetry" in data
        assert "metadata" in data


class TestAlarms:
    """Test alarm endpoints."""

    @pytest.mark.asyncio
    async def test_list_active_alarms(self, async_client: AsyncClient):
        """Test listing active alarms."""
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )
        token = login_response.json()["access_token"]

        response = await async_client.get(
            "/api/v1/industrial/alarms",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "alarms" in data
        assert "total" in data


class TestDashboard:
    """Test dashboard endpoints."""

    @pytest.mark.asyncio
    async def test_get_dashboard_overview(self, async_client: AsyncClient):
        """Test getting dashboard overview."""
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )
        token = login_response.json()["access_token"]

        response = await async_client.get(
            "/api/v1/dashboard/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "machine_status" in data
        assert "telemetry_widgets" in data
        assert "alarm_widget" in data
        assert "kpi_widgets" in data
        assert "trend_widgets" in data

    @pytest.mark.asyncio
    async def test_get_machine_status(self, async_client: AsyncClient):
        """Test getting machine status summary."""
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )
        token = login_response.json()["access_token"]

        response = await async_client.get(
            "/api/v1/dashboard/machine-status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        status_data = data["status"]
        assert "total" in status_data
        assert "online" in status_data


class TestAIStubs:
    """Test AI integration stubs."""

    @pytest.mark.asyncio
    async def test_predict_anomaly(self, async_client: AsyncClient):
        """Test anomaly prediction stub."""
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )
        token = login_response.json()["access_token"]

        machine_response = await async_client.post(
            "/api/v1/industrial/machines",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "AI Machine",
                "serial_number": "TM-AI-001",
            },
        )
        machine_id = machine_response.json()["id"]

        response = await async_client.post(
            "/api/v1/industrial/ai/anomaly/predict",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "machine_id": machine_id,
                "telemetry_window": [
                    {"name": "temperature", "value": 85.0, "unit": "°C", "timestamp": "2024-01-15T10:30:00Z"},
                ],
                "sensitivity": 0.95,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "anomaly_detected" in data
        assert "anomaly_score" in data
        assert "model_version" in data

    @pytest.mark.asyncio
    async def test_predict_rul(self, async_client: AsyncClient):
        """Test RUL prediction stub."""
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )
        token = login_response.json()["access_token"]

        machine_response = await async_client.post(
            "/api/v1/industrial/machines",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "RUL Machine",
                "serial_number": "TM-RUL-001",
            },
        )
        machine_id = machine_response.json()["id"]

        response = await async_client.post(
            "/api/v1/industrial/ai/rul/predict",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "machine_id": machine_id,
                "telemetry_history": [
                    {"name": "temperature", "value": 75.0, "unit": "°C", "timestamp": "2024-01-15T10:30:00Z"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "predicted_rul_hours" in data
        assert "confidence" in data
        assert "model_version" in data