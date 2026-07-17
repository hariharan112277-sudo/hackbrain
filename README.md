# Phase 5 Enterprise Integration Package: Industrial Operating Brain (IOB)

This is the complete, production-grade, and unified implementation of **Phase 5: Backend Integration, Performance & Security Optimization** for Member 1. This phase establishes the central orchestration layer — connecting our core FastAPI services to Member 2's Industrial IoT and repository layers, while preparing interfaces for Member 3's AI and Member 4's frontend UI.

**Phase 0 Remediation Applied:**
- Async SQLAlchemy 2.0 session management (`postgresql+asyncpg://` required)
- Redis Pub/Sub event bus for non-blocking Track A → Track B notifications
- `X-Correlation-ID` propagation middleware
- Docker resource limits (`cpus`, `memory`) on AI and API containers
- Canonical `shared/schemas/` contract alignment
- MQTT broker horizontal scaling documentation added (see `docs/architecture/mqtt_scaling.md`)

## Directory Structure

```
Phase5_Backend_Integration/
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── industrial.py
│   │   └── dashboard.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── logging_config.py
│   │   └── security.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── interfaces.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── industrial.py
│   │   └── dashboard.py
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py
│       ├── user_service.py
│       ├── industrial_service.py
│       └── dashboard_service.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_integration.py
│   └── test_contracts.py
├── docs/
│   ├── backend_integration.md
│   ├── repository_usage.md
│   ├── api_validation.md
│   ├── security.md
│   ├── performance.md
│   └── testing.md
├── reports/
│   ├── phase5_project_review.md
│   ├── phase5_acceptance.md
│   └── quality_assurance.md
└── pyproject.toml
```

## Integration Instructions

1. Copy these files into your existing project workspace
2. Merge with your existing `app/` directory structure
3. Update your `pyproject.toml` with the new dependencies
4. Run tests to verify integration: `pytest tests/ -v`
5. Compress locally using: `zip -r Phase5_Backend_Integration_Enterprise_Package.zip Phase5_Backend_Integration/`

## Key Integration Points

- **Member 2 (IoT & Database)**: Consumes `IMachineRepository`, `ITelemetryRepository`, `IAlarmRepository`, `IMetadataRepository` interfaces
- **Member 3 (AI Subsystem)**: Standardized endpoints with stubs for anomaly status and RUL predictions
- **Member 4 (Frontend/UI)**: Strict JSON output structures mapped to Pydantic schemas

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run the application
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v --cov=app
```

## Database Driver Note

The Phase 0 remediation mandates `postgresql+asyncpg://` for all async SQLAlchemy 2.0 connections. Ensure your `.env` and `docker-compose.yml` use this prefix. The old `postgresql+psycopg2://` sync driver is deprecated for Track A async endpoints and will cause runtime connection failures under high telemetry load.