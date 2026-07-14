# Integration Notes

This document describes how Phase 4 integrates with the existing IOB repository.

## Merge Instructions

1. Copy the contents of `Phase4_Backend_APIs/` over the existing project root.
2. Review the modified files (`app/main.py`, `app/core/config.py`, `app/core/health.py`, `pyproject.toml`).
3. Install or update dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the application:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
5. Run tests:
   ```bash
   pytest tests/ -v
   ```

## Integration Points

| Phase 4 Component | Existing IOB Component |
|-------------------|------------------------|
| `app.repositories.adapters` | `integration.services`, `database.connection` |
| `app.core.health` | `database.connection.connection_manager.check_health()` |
| `app.services.industrial_service` | `integration.interfaces` repository contracts |
| `app.main` | Existing factory, middleware, exception handlers |

## Repository Mode

- `stub`: standalone, no database required.
- `integration`: delegates to Member 2 services and SQLAlchemy repositories.

## Boundary Compliance

- Member 1 does not import SQLAlchemy ORM models directly in controllers.
- Member 1 consumes repository interfaces via FastAPI `Depends`.
- Member 2 retains ownership of persistence logic and MQTT ingestion.

## Notes for Member 3 (AI)

The `/api/v1/industrial/machines/{id}/telemetry/history` endpoint returns clean,
paginated time-series JSON suitable for anomaly detection and predictive
maintenance model training.
