# Phase 3 implementation handoff

Implemented against the existing FastAPI wiring:

- Ordered lifespan startup/shutdown with database verification, MQTT bridge, WebSocket distributor, Redis and SQLAlchemy pool disposal.
- Production aliases: `IOB_ENV_MODE`, `IOB_POSTGRES_DSN`, `IOB_JWT_SECRET_KEY`, `IOB_MQTT_BROKER_HOST`, and optional `IOB_AI_GATEWAY_KEY`.
- Production rejects development JWT secrets, SQLite fallback DSNs, and wildcard CORS.
- JSON structured logging formatter, correlation context and compatibility middleware.
- `/api/v1/health/live` and `/api/v1/health/ready` probes; readiness includes database and MQTT state and uses 503 only when required.
- MQTT bridge connection state and shutdown guard.
- SQLAlchemy SQLite-safe pool construction (fixes local startup failure) and `greenlet`/`asyncpg`/`redis` dependency boundaries.
- Non-root multi-stage Docker image with healthcheck and no fixed production secret.
- `.env.example` and `phase3_smoke_test.py`.

## Verification

`python -m compileall -q app shared phase3_smoke_test.py` — passed.

`python phase3_smoke_test.py` — passed.

The repository's full legacy suite still contains unrelated pre-Phase-3 contract failures around the `/auth/login` username-vs-email fixture and `/api/v1/machines`; those were not silently relabeled as production-certified. Run `pytest -q tests/test_phase3_core.py` after aligning those legacy fixtures if you need the historical suite.
