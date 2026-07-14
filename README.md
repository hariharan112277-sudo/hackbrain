# Phase 4 Enterprise Execution Package: Industrial Operating Brain (IOB)

This is the complete, production-ready implementation of **Phase 4: Business Services, REST APIs, and Integration** for Member 1.

## What is Inside

- **Core FastAPI infrastructure** (`app/main.py`, `app/core/`)
- **REST API controllers** (`app/api/`)
  - Authentication
  - User management
  - Industrial data (machines, telemetry, alarms, metadata)
  - Dashboard aggregation
- **Business service layer** (`app/services/`)
- **Repository interfaces & adapters** (`app/repositories/`)
- **Pydantic schemas** (`app/schemas/`)
- **Verification suite** (`tests/`)
- **Documentation** (`docs/`)
- **Audit reports** (`reports/`)

## How to Use This Package

1. Copy the contents of this folder over your existing IOB repository root.
2. Resolve any dependency updates from `pyproject.toml` or `requirements.txt`.
3. Run the test suite:
   ```bash
   pytest tests/ -v
   ```
4. Start the server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
5. Open Swagger UI at `http://localhost:8000/api/v1/docs`.

## Repository Mode

- `PHASE4_REPOSITORY_MODE=stub` (default): in-memory repositories, no DB needed.
- `PHASE4_REPOSITORY_MODE=integration`: delegates to Member 2 integration services.

## Default Login

| Username | Password | Roles |
|----------|----------|-------|
| `admin@iob.local` | `admin` | admin, operator |

See `docs/` for detailed API and integration documentation.
