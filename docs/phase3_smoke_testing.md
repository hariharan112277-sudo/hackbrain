# Phase 3 Smoke Testing Documentation

## Purpose

This document captures the smoke testing and runtime verification process executed for the Industrial Operating Brain (IOB) backend during Phase 3. It aligns with the Phase 3 Engineering Handbook requirements.

## Scope

Verification covers:
- FastAPI application initialization (`app/main.py`)
- REST API endpoint responses (`/health`, `/auth/login`, `/assets`, `/alerts`, `/dashboard/summary`)
- Database transaction management (`PostgreSQL 16.2` / `AsyncSession`)
- JWT authentication and authorization (`apps/core/dependencies.py`)
- AI Gateway proxy (`app/realtime_ai/gateway/protocol_translator.py`)
- MQTT telemetry bridge (`app/mqtt_bridge.py`)
- WebSocket real-time streams (`app/realtime_ai/streaming/workers.py`, `app/api/ws.py`)
- Background worker stability (lifespan hooks in `app/main.py`)

## Execution Steps

1. Initialize the primary web server with environment configurations.
2. Execute `tests/smoke_tests.py` using `pytest`.
3. Inspect `tests/test_ai_proxy.py`, `tests/test_assets.py`, and `tests/test_stage2_realtime.py`.
4. Monitor container boot trace logs for `IOB-BOOT`, `IOB-DB`, `IOB-REDIS`, `IOB-MQTT`, and `IOB-UVICORN` markers.
5. Verify log outputs in `reports/phase3_smoke_testing_report.md`.

## Integration Points

- `app/main.py` registers `lifespan` manager that starts MQTT bridge and WebSocket distributor.
- `app/realtime_ai/gateway/protocol_translator.py` handles payload translation without DB blocking.
- `app/realtime_ai/streaming/workers.py` processes telemetry using `AsyncSession`.
- `tests/smoke_tests.py` validates the full matrix programmatically.

## References

- Phase 3 Engineering Handbook (pasted specification)
- `tests/smoke_tests.py`
- `reports/phase3_smoke_testing_report.md`
- `app/main.py`
- `docs/phase3_smoke_testing.md` (this file)
