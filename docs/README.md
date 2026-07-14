# Phase 4 Enterprise Backend APIs

This package implements **Phase 4: Business Services, REST APIs, and Integration** for the Industrial Operating Brain (IOB) platform.

## Scope

- **Member 1 (Self):** Core FastAPI infrastructure, business service orchestration, REST controllers, routing, JWT/security enforcement, user management.
- **Member 2:** MQTT ingestion, time-series industrial database, and repository layer. Member 1 consumes abstract repository interfaces via dependency injection.
- **Member 3 (AI):** Anomaly detection and predictive maintenance models. Phase 4 services call abstract stubs for AI predictions to remain decoupling-compliant.
- **Member 4 (Frontend):** UI. Phase 4 provides complete REST endpoints returning clean, typed JSON matching UI expectations.

## Directory Layout

```
app/
  api/              REST controllers (auth, users, industrial, dashboard)
  core/             Configuration, security, logging, exception handling
  repositories/     Abstract interfaces + concrete stubs/adapters
  schemas/          Pydantic request/response models
  services/         Business service orchestration layer
tests/              Verification suite
```

## Quick Start

1. Merge the contents of this folder into the existing IOB repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # or
   poetry install
   ```
3. Run the application:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
4. Run the verification suite:
   ```bash
   pytest tests/ -v
   ```

## API Documentation

- [Authentication](./authentication.md)
- [User Management](./api_reference.md#user-management)
- [Machine API](./machine_api.md)
- [Historical Telemetry API](./historical_api.md)
- [Alarm API](./alarm_api.md)
- [Metadata API](./metadata_api.md)
- [Dashboard API](./dashboard_api.md)
- [Service Layer](./service_layer.md)
- [Testing](./testing.md)
- [Integration Notes](./integration.md)
