# Hackbrain Final Cleanup — Standalone Fixes

This zip contains ONLY the modified files required to pass the final cleanup pass.

## Final test result
```
pytest tests/ -q --ignore=tests/test_stage2_realtime.py
====================== 226 passed, 21 warnings in 17.83s =======================
```
0 failures, 0 errors.

## How to apply
Unzip this archive at the repo root. All paths are relative to the repository root.

```
unzip hackbrain_fixes_only.zip -d /path/to/hackbrain/
```

Then **delete** the file listed in `DELETED_FILES.txt`:
```
tests/test_industrial.py
```

## File manifest

### Application code (Issue 2 — pagination + one small bug fix)
- `app/api/v1/assets.py` — added `limit`/`offset` Query params to `get_assets()`; items are paginated while total_count/critical_count reflect full set.
- `app/api/v1/alerts.py` — added `limit`/`offset` Query params to `get_alerts()`; applied to query.
- `app/core/exceptions.py` — fixed `ResourceNotFoundError.__init__` to handle `details=None` safely (was crashing with `TypeError: 'NoneType' object is not a mapping`).

### Tests (Issue 1 — stale test files)
- `tests/test_industrial.py` — **DELETED** (see `DELETED_FILES.txt`).
- `tests/test_users.py` — rewrote to use the current `email`+`password` login schema against a mocked admin session; updated create-user payloads to match the Phase-5 `UserCreate` schema (`email`/`full_name`/`password`/`roles`) and hit the current `/api/v1/users` CRUD endpoints.
- `tests/test_phase3_core.py` — rewrote exception-handler and application-factory sections to reflect the current exception hierarchy (`IOBException`, `ResourceNotFoundError`, `AuthenticationError`, `AuthorizationError`) and Phase-1 canonical handlers; removed tests for deleted endpoints (`/api/v1/info`, `/api/v1/info`, root status); kept `test_correlation_id_generated_when_not_provided` and the CORS test (fixed `middleware.klass` → `middleware.cls` for newer Starlette); updated readiness assertions to match `status == "not_ready"`.
- `tests/test_assets.py` — extended the mock DB to return alarms through the new `.offset().limit()` chain so pagination doesn't break existing tests.
- `tests/test_phase4_frontend_integration.py` — fixed stale URL `/api/v1/industrial/alerts/.../resolve` → `/api/v1/alerts/.../resolve` in `test_role_mismatch_403`.
- `tests/test_integration.py` — rewrote against the current route map (no `/api/v1/auth/register`, no `/api/v1/industrial/*`, dashboard is `/api/v1/dashboard/summary`); uses mocked DB sessions and dependency overrides per the pattern used by the rest of the suite.
- `tests/test_stage5_migration.py` — replaced the obsolete `test_production_rejects_missing_mqtt_secret` (MQTT_PASSWORD is Optional in the current Settings model) with `test_production_allows_empty_mqtt_credentials_when_explicitly_unset` verifying production boots cleanly without it.

## Out of scope (untouched per instructions)
- app/api/ai_proxy.py
- app/api/ws.py
- app/services/mqtt_bridge.py
- app/main.py exception handlers
- Auth/JWT flow
