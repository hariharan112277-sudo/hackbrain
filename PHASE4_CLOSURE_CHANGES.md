# Phase 4 — Claude Evaluation Closure Matrix (Applied & Verified)

This document records the four findings from the Final Acceptance "Claude
Evaluation Closure Matrix" and the exact changes made to the IOB backend so the
repo is left in the signed-off (CLOSED) state.

All paths are relative to the repository root. Extract/drop these into the
existing wiring — they are already integrated in this tree.

---

## 1. Validation Handler 500 Crash — CLOSED

- **Root cause:** Pydantic surfaced raw `bytes` (binary injection / corrupted
  UTF-8) inside `RequestValidationError.errors()`; the old inline handler passed
  those straight to `JSONResponse`, so `json.dumps` raised
  `TypeError: Object of type bytes is not JSON serializable` and escalated a
  client 4xx into a 500.
- **Resolution:** Exception fields are wrapped with FastAPI's
  `jsonable_encoder` plus a recursive `sanitize_payload()` helper that decodes
  raw bytes (`errors="backslashreplace"`) and normalizes UUID / datetime /
  Decimal / Enum / set types before serialization.
- **Files (already wired, verified):**
  - `app/core/exceptions.py` — `sanitize_payload()`, `create_error_response()`,
    `request_validation_exception_handler()`, `pydantic_validation_exception_handler()`
  - `app/main.py` — registers the handlers via `add_exception_handler(...)`
- **Verification:** `tests/test_phase1_exception_hardening.py`
  (`test_val002_binary_injection`, `test_request_validation_with_raw_bytes`,
  `test_sanitize_payload_handles_non_utf8_bytes`) → binary body now returns
  **422**, never 500.

## 2. Legacy Route Proliferation — CLOSED

- **Root cause:** A redundant legacy route module lived at `app/api/industrial.py`
  (the `/api/v1/industrial/*` surface). It was never mounted in `app/main.py`
  and was not imported by any other module — pure dead code.
- **Resolution:** The legacy route module and its orphaned test were **deleted**;
  the legitimate schema/service (`app/schemas/industrial.py`,
  `app/services/industrial_service.py`) are kept because the rest of the app
  (dashboard, alerts) depends on them.
- **Files changed:**
  - `app/api/industrial.py` — **DELETED**
  - `tests/test_industrial.py` — **DELETED** (orphaned test for the removed route)
- **Verification:** `app.openapi()` no longer exposes any `/api/v1/industrial`
  path (confirmed by schema inspection). No module imports `app.api.industrial`.

## 3. Workspace Clutter / Debris — CLOSED

- **Root cause:** A single-use script `parser.py` was left at the repository
  root. It used a package-relative import (`from .models import ...`) that only
  resolves inside a package, so it was broken debris at the root level.
- **Resolution:** `parser.py` removed from the root. Valid, reusable scripts
  already live under `scripts/` (`database_seed.py`, `export_openapi.py`,
  `generate_ts_models.py`, `seed_demo_data.py`).
- **Files changed:**
  - `parser.py` — **DELETED**
- **Verification:** Full repository-structure check — no orphan `parser.py` at
  root; nothing else imports it.

## 4. Uncaught DB Exceptions — CLOSED

- **Root cause:** Raw `SQLAlchemyError` output (incl. stack traces) could leak to
  clients and escalate to 500.
- **Resolution:** Explicit global transaction exception interceptors map DB
  failures to clean envelopes — `IntegrityError` → 409
  `DATABASE_INTEGRITY_VIOLATION`, other `SQLAlchemyError` → 503
  `DATABASE_UNAVAILABLE`. A global `Exception` handler guarantees every
  unhandled error returns the strict `{"success": false, "error": ...}` contract
  with **no traceback leakage**.
- **Files (already wired, verified):**
  - `app/core/exceptions.py` — `sqlalchemy_exception_handler()`,
    `general_exception_handler()`
  - `app/main.py` — `add_exception_handler(SQLAlchemyError, ...)` and
    `add_exception_handler(Exception, ...)`
- **Verification:** `tests/test_phase1_exception_hardening.py`
  (`test_sqlalchemy_integrity_conflict`, `test_sqlalchemy_generic_unavailable`,
  `test_global_exception_safe_schema`, `test_val012_integrity_conflict_via_handler`)
  → 409 / 503 envelopes, no `Traceback` / `RuntimeError` in body.

---

## How to execute / verify

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest tests/test_phase1_exception_hardening.py -v   # VAL-001 .. VAL-012
pytest -q                                          # full harness (stub repos + SQLite)
python -c "from app.main import app; print(app.openapi().get('paths').keys())"  # no /industrial
```

## Net change set (worked + new files)

- **New:** `PHASE4_CLOSURE_CHANGES.md` (this file)
- **Deleted:** `app/api/industrial.py`, `tests/test_industrial.py`, `parser.py`
- **Already-present & verified (Phase 4 wiring):** `app/main.py`,
  `app/core/exceptions.py`, `app/core/payload_guard.py`, `app/core/timeutils.py`,
  `app/core/config.py`, `app/api/auth.py`, `app/api/ai_proxy.py`, `app/api/ws.py`,
  `scripts/generate_ts_models.py`, `tests/test_phase4_frontend_integration.py`.
