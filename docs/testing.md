# Testing Guide

The Phase 4 verification suite is located in `tests/`.

## Run Tests

```bash
# All Phase 4 tests
pytest tests/ -v

# Specific module
pytest tests/test_auth.py -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

## Test Structure

| File | Coverage |
|------|----------|
| `test_auth.py` | Login, refresh, token introspection, `/me` |
| `test_users.py` | User CRUD, role-based access control |
| `test_industrial.py` | Machines, telemetry, alarms, metadata, dashboard |

## Fixtures

- `app`: FastAPI application instance.
- `client`: per-test `TestClient`.
- `admin_token`: JWT for the default admin account.
- `auth_headers`: pre-built `Authorization` header for the admin token.

## Stub Mode

By default, tests run against the in-memory stub repositories (`PHASE4_REPOSITORY_MODE=stub`).
This ensures the test suite is fast, deterministic, and does not require a running database.

## Integration Tests

To validate the real Member 2 wiring, set:

```bash
export PHASE4_REPOSITORY_MODE=integration
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/iob
pytest tests/test_industrial.py -v
```
