"""
Pytest Configuration and Fixtures
Phase 5: Test configuration with stub repositories.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from app.main import create_app
from app.core.dependencies import initialize_stub_repositories, reset_repository_subsystem
from app.core.config import settings


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment."""
    original_values = {
        "DEBUG": settings.DEBUG,
        "SECRET_KEY": settings.SECRET_KEY,
        "ENV": settings.ENV,
        "ENVIRONMENT": settings.ENVIRONMENT,
        "USE_STUB_REPOSITORIES": settings.USE_STUB_REPOSITORIES,
    }
    settings.DEBUG = True
    settings.SECRET_KEY = "test-secret-key-for-testing-only-32-chars-minimum"
    settings.ENV = "test"
    settings.ENVIRONMENT = "test"
    settings.USE_STUB_REPOSITORIES = True
    initialize_stub_repositories()
    yield
    reset_repository_subsystem()
    for name, value in original_values.items():
        setattr(settings, name, value)


@pytest.fixture(scope="function")
def app():
    """Create test app instance."""
    return create_app()


@pytest_asyncio.fixture
async def async_client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_machine_repo():
    """Mock machine repository."""
    return AsyncMock()


@pytest.fixture
def mock_telemetry_repo():
    """Mock telemetry repository."""
    return AsyncMock()


@pytest.fixture
def mock_alarm_repo():
    """Mock alarm repository."""
    return AsyncMock()


@pytest.fixture
def mock_metadata_repo():
    """Mock metadata repository."""
    return AsyncMock()


@pytest.fixture
def mock_user_repo():
    """Mock user repository."""
    return AsyncMock()


@pytest.fixture
def mock_role_repo():
    """Mock role repository."""
    return AsyncMock()


@pytest.fixture
def mock_permission_repo():
    """Mock permission repository."""
    return AsyncMock()


# Test data fixtures
@pytest.fixture
def sample_machine_data():
    """Sample machine data for testing."""
    return {
        "id": "test-machine-1",
        "name": "Test Machine 1",
        "serial_number": "TM-001",
        "model": "TM-100",
        "manufacturer": "Test Corp",
        "location": "Factory A",
        "status": "online",
        "tags": {"env": "test"},
    }


@pytest.fixture
def sample_telemetry_data():
    """Sample telemetry data for testing."""
    return {
        "machine_id": "test-machine-1",
        "timestamp": "2024-01-15T10:30:00Z",
        "metrics": [
            {"name": "temperature", "value": 75.5, "unit": "°C"},
            {"name": "pressure", "value": 8.2, "unit": "bar"},
        ],
    }


@pytest.fixture
def sample_alarm_data():
    """Sample alarm data for testing."""
    return {
        "id": "alarm-1",
        "machine_id": "test-machine-1",
        "alarm_code": "HIGH_TEMP",
        "message": "Temperature exceeded threshold",
        "severity": "high",
        "status": "active",
        "source": "sensor-1",
        "created_at": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user-1",
        "email": "test@example.com",
        "full_name": "Test User",
        "password_hash": "$2b$12$hashedpassword",
        "is_active": True,
        "roles": ["operator"],
        "permissions": ["machines:read", "telemetry:read"],
        "created_at": "2024-01-01T00:00:00Z",
    }