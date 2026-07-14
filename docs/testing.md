# Testing Strategy
## Phase 5: Unit, Integration, Contract, and Load Testing

### Overview

This document describes the comprehensive testing strategy for Phase 5, ensuring reliability and correctness of the IOB backend integration.

### Test Pyramid

```
                    ┌─────────────┐
                    │   E2E/UI    │  ← Few, slow, high confidence
                    └─────────────┘
              ┌─────────────────────┐
              │   Integration       │  ← API, DB, external services
              └─────────────────────┘
        ┌───────────────────────────────┐
        │   Contract Tests              │  ← Schema, API contracts
        └───────────────────────────────┘
  ┌─────────────────────────────────────────┐
  │   Unit Tests                            │  ← Many, fast, isolated
  └─────────────────────────────────────────┘
```

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures & configuration
├── test_integration.py      # End-to-end API integration tests
├── test_contracts.py        # Schema & contract validation tests
├── test_unit/               # Unit tests (per module)
│   ├── test_auth_service.py
│   ├── test_user_service.py
│   ├── test_industrial_service.py
│   └── test_dashboard_service.py
└── test_load/               # Load/performance tests
    └── locustfile.py
```

### Running Tests

```bash
# All tests with coverage
pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Specific test suites
pytest tests/test_integration.py -v
pytest tests/test_contracts.py -v
pytest tests/test_unit/ -v

# With specific markers
pytest -m "not slow"          # Skip slow tests
pytest -m "integration"       # Only integration tests
pytest -m "contract"          # Only contract tests

# Parallel execution
pytest -n auto                # Auto-detect CPU cores

# Verbose with output
pytest tests/ -v -s --tb=short
```

### Unit Testing

#### Service Layer Tests
```python
# tests/test_unit/test_industrial_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from app.services.industrial_service import IndustrialService
from app.schemas.industrial import MachineCreate

@pytest.fixture
def mock_repos():
    return {
        "machine": AsyncMock(),
        "telemetry": AsyncMock(),
        "alarm": AsyncMock(),
        "metadata": AsyncMock(),
    }

@pytest.fixture
def industrial_service(mock_repos):
    return IndustrialService(
        machine_repo=mock_repos["machine"],
        telemetry_repo=mock_repos["telemetry"],
        alarm_repo=mock_repos["alarm"],
        metadata_repo=mock_repos["metadata"],
    )

class TestIndustrialService:
    @pytest.mark.asyncio
    async def test_get_machine_telemetry_flow(self, industrial_service, mock_repos):
        machine_id = uuid4()
        mock_repos["machine"].get_by_id.return_value = {
            "id": str(machine_id), "name": "Test Machine", "status": "online"
        }
        mock_repos["telemetry"].get_latest_telemetry.return_value = {
            "metrics": [{"name": "temp", "value": 75.0}]
        }
        mock_repos["metadata"].get_machine_metadata.return_value = {"firmware": "1.0"}
        
        result = await industrial_service.get_machine_telemetry_flow(machine_id)
        
        assert result["machine_id"] == str(machine_id)
        assert result["name"] == "Test Machine"
        assert "telemetry" in result
        assert "metadata" in result
    
    @pytest.mark.asyncio
    async def test_get_machine_not_found(self, industrial_service, mock_repos):
        mock_repos["machine"].get_by_id.return_value = None
        
        with pytest.raises(ResourceNotFoundError):
            await industrial_service.get_machine_telemetry_flow(uuid4())
```

#### Repository Contract Tests
```python
# tests/test_unit/test_repository_contracts.py
import pytest
from app.repositories.interfaces import IMachineRepository

class TestMachineRepositoryContract:
    """Tests that any IMachineRepository implementation satisfies the contract."""
    
    @pytest.fixture
    def repo(self) -> IMachineRepository:
        # Override in conftest with actual implementation
        pass
    
    @pytest.mark.asyncio
    async def test_crud_lifecycle(self, repo: IMachineRepository):
        # Create
        machine = await repo.create({
            "name": "Test", "serial_number": "TEST-001", "status": "online"
        })
        assert machine["id"] is not None
        
        # Read
        retrieved = await repo.get_by_id(machine["id"])
        assert retrieved["serial_number"] == "TEST-001"
        
        # Update
        updated = await repo.update(machine["id"], {"status": "maintenance"})
        assert updated["status"] == "maintenance"
        
        # List
        machines = await repo.list_machines(limit=10)
        assert len(machines) >= 1
        
        # Delete
        deleted = await repo.delete(machine["id"])
        assert deleted is True
        
        # Verify deleted
        assert await repo.get_by_id(machine["id"]) is None
```

### Integration Testing

#### API Integration Tests
```python
# tests/test_integration.py
import pytest
from httpx import AsyncClient

class TestAuthenticationIntegration:
    @pytest.mark.asyncio
    async def test_full_auth_flow(self, async_client: AsyncClient):
        # 1. Register
        register_resp = await async_client.post("/api/v1/auth/register", json={
            "email": "integration@test.com",
            "password": "SecurePass123!",
            "full_name": "Integration Test",
        })
        assert register_resp.status_code == 201
        tokens = register_resp.json()
        
        # 2. Access protected endpoint
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        machines_resp = await async_client.get("/api/v1/industrial/machines", headers=headers)
        assert machines_resp.status_code == 200
        
        # 3. Refresh token
        refresh_resp = await async_client.post("/api/v1/auth/refresh", json={
            "refresh_token": tokens["refresh_token"]
        })
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()
        assert new_tokens["access_token"] != tokens["access_token"]
        
        # 4. Use new token
        headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
        me_resp = await async_client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
```

#### Database Integration Tests
```python
# tests/test_integration_db.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
async def db_session():
    # Use test database
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.rollback()  # Clean up

@pytest.mark.asyncio
async def test_machine_repository_integration(db_session):
    from app.repositories.adapters import PostgresMachineRepository
    
    repo = PostgresMachineRepository(db_session)
    
    # Test full CRUD
    machine = await repo.create({
        "name": "Integration Machine",
        "serial_number": "INT-001",
        "status": "online",
    })
    assert machine["id"] is not None
    
    retrieved = await repo.get_by_id(machine["id"])
    assert retrieved["name"] == "Integration Machine"
```

### Contract Testing

#### Schema Validation Tests
```python
# tests/test_contracts.py
import pytest
from pydantic import ValidationError
from app.schemas.industrial import MachineCreate, MachineResponse, MachineStatus

def test_machine_create_schema_valid():
    machine = MachineCreate(
        name="Valid Machine",
        serial_number="VM-001",
        status=MachineStatus.ONLINE,
    )
    assert machine.name == "Valid Machine"

def test_machine_create_schema_invalid():
    # Empty name
    with pytest.raises(ValidationError) as exc:
        MachineCreate(name="", serial_number="VM-001")
    assert "name" in str(exc.value)
    
    # Invalid status
    with pytest.raises(ValidationError):
        MachineCreate(name="Test", serial_number="VM-001", status="invalid")

def test_machine_response_schema():
    from uuid import uuid4
    from datetime import datetime
    
    response = MachineResponse(
        id=uuid4(),
        name="Test",
        serial_number="TM-001",
        status=MachineStatus.ONLINE,
        tags={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    assert response.id is not None
```

#### API Response Contract Tests
```python
@pytest.mark.asyncio
async def test_machine_list_response_contract(async_client, auth_headers):
    response = await async_client.get("/api/v1/industrial/machines", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    # Validate structure
    assert "machines" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    
    # Validate each machine
    for machine in data["machines"]:
        MachineResponse(**machine)  # Will raise if invalid
```

### Test Fixtures

#### Conftest Fixtures
```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.core.dependencies import initialize_stub_repositories

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    initialize_stub_repositories()
    yield

@pytest_asyncio.fixture
async def async_client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture
def auth_headers(async_client):
    # Create test user and return auth headers
    async def _get_headers(email="test@example.com", password="SecurePass123!"):
        # Register
        await async_client.post("/api/v1/auth/register", json={
            "email": email, "password": password, "full_name": "Test User"
        })
        # Login
        resp = await async_client.post("/api/v1/auth/login", json={
            "email": email, "password": password
        })
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return _get_headers
```

### Mocking External Services

#### AI Service Mock
```python
# tests/mocks/ai_service.py
from unittest.mock import AsyncMock
from app.services.industrial_service import IndustrialService

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing IndustrialService AI methods."""
    with patch("app.services.industrial_service.AIServiceClient") as mock:
        mock.predict_anomaly = AsyncMock(return_value={
            "anomaly_detected": False,
            "anomaly_score": 0.05,
            "confidence": 0.95,
            "model_version": "test-v1",
        })
        mock.predict_rul = AsyncMock(return_value={
            "predicted_rul_hours": 8760,
            "confidence": 0.90,
            "model_version": "test-v1",
        })
        yield mock
```

### Continuous Integration

#### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        ports: ["6379:6379"]
        options: --health-cmd "redis-cli ping" --health-interval 10s --health-timeout 5s --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          pip install -e ".[test]"
      
      - name: Run unit tests
        run: pytest tests/test_unit/ -v --cov=app --cov-report=xml
      
      - name: Run integration tests
        run: pytest tests/test_integration.py -v
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost/test_db
          REDIS_URL: redis://localhost:6379/0
      
      - name: Run contract tests
        run: pytest tests/test_contracts.py -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### Test Coverage Targets

| Layer | Target | Current |
|-------|--------|---------|
| Unit Tests | > 90% | ✅ |
| Integration Tests | > 80% | ✅ |
| Contract Tests | 100% schemas | ✅ |
| Overall | > 85% | ✅ |

### Debugging Tests

```bash
# Run single test with full output
pytest tests/test_integration.py::TestAuthentication::test_login_user -v -s

# Drop into debugger on failure
pytest tests/ --pdb

# Show slowest tests
pytest tests/ --durations=10

# Run with specific log level
pytest tests/ -v --log-cli-level=DEBUG
```