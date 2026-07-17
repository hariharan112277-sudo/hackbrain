# Phase 2 Change Manifest

## Added / relocated
- `app/api/v1/assets.py` — canonical ORM-backed asset API
- `app/api/v1/alerts.py` — canonical ORM-backed alert API
- `app/core/database/engine.py` — database engine moved into the `app` namespace
- `app/services/alert_service.py` — service moved into the `app` namespace
- `scripts/database_seed.py` — seed utility under the scripts directory
- `docs/API_CONTRACT_V1.md` — stable validation/database error contracts

## Updated wiring
- `app/main.py` mounts only `/api/v1/assets` and `/api/v1/alerts` for these operations.
- `app/database.py`, `app/core/health.py`, and `tests/conftest.py` use `app.core` imports.
- `tests/test_assets.py` verifies canonical route paths.
- `.gitignore` excludes Python caches, coverage output, local databases, and `.env`.

## Removed
- `apps/` duplicate package tree
- `app/api/industrial.py`
- `tests/test_industrial.py`
- `parser.py`
- `duplicate_detector.py`
- `metadata_enricher.py`

## Verification performed
- Python compilation of `app/`: passed
- OpenAPI route check: canonical assets/alerts present; industrial aliases absent
- `pytest -q tests/test_assets.py --no-cov`: **12 passed**

The historical report's “105+ tests” count was not reproduced because the current repository contains a different suite and several legacy tests target the intentionally retired route/package surface.
