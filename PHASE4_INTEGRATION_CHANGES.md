# Phase 4 — Frontend Integration & API Contract Validation

## Implementation Change Log

This package contains the modified and new files implementing the Phase 4
Engineering Handbook recommendations against the existing IOB backend wiring.
All files are placed at paths matching the project directory tree — extract
the zip over the repository root to apply.

---

## 1. New Files

| File | Purpose |
|------|---------|
| `app/core/timeutils.py` | **R-4.4.1** — `utc_iso()` helper enforcing strict UTC ISO 8601 (`YYYY-MM-DDTHH:mm:ssZ`) on all system timestamps. |
| `app/core/payload_guard.py` | **R-4.5.1** — Pure-ASGI middleware rejecting request bodies over 10MB on the `/api/v1/ai` prefix with a standard 413 error envelope. Guards both `Content-Length` and chunked streams. |
| `scripts/generate_ts_models.py` | **R-4.1.1** — Generates TypeScript interfaces directly from the backend OpenAPI/Pydantic schema. Wire into the frontend build (`prebuild` npm script / CI step). |
| `frontend/src/types/api-models.generated.ts` | Sample generated output (17 models) proving the R-4.1.1 pipeline works end-to-end. |
| `tests/test_phase4_frontend_integration.py` | Phase 4 verification suite (24 tests) covering Sections 2, 3, 4, 5, 6, 8, 9 of the handbook. |
| `PHASE4_INTEGRATION_CHANGES.md` | This change log. |

## 2. Modified Files

### `app/main.py`
- **Section 9 (CORS)** — Replaced wildcard `allow_methods=["*"]` / `allow_headers=["*"]`
  with explicit allow-lists (`GET/POST/PUT/PATCH/DELETE/OPTIONS`,
  `Authorization`, `Content-Type`, `X-Correlation-ID`, `X-Requested-With`)
  and exposed `X-Correlation-ID` to browser clients.
- **R-4.5.1** — Mounted `PayloadSizeLimitMiddleware` on the `/api/v1/ai` prefix.
- **Wiring fix** — The Stage 3 industrial router was imported but never mounted,
  leaving `/api/v1/industrial/*` unreachable (404). Now mounted at
  `/api/v1/industrial` — this repaired 10 pre-existing failing tests in
  `tests/test_assets.py`.

### `app/core/config.py`
- Added Phase 4 settings: `AI_GATEWAY_MAX_PAYLOAD_BYTES` (10MB),
  `WS_BROADCAST_BATCH_MS` / `WS_BROADCAST_BATCH_MAX` (R-4.6.1 batching),
  `AUTH_COOKIE_*` (R-4.3.1 HTTP-only cookie issuance), `MAX_PAGE_LIMIT` (R-4.2.1).

### `app/api/auth.py`
- **R-4.3.1** — `/login` and `/refresh` now mirror the access token into a
  secure HTTP-only cookie (`iob_access_token`) so browser clients can avoid
  script-accessible storage (XSS protection). JSON contract unchanged.
- **Session Termination Safety (Section 3)** — Added `POST /api/v1/auth/logout`
  which clears the auth cookie and gives frontends an explicit termination hook.

### `app/api/ai_proxy.py`
- **Section 5** — All AI Gateway inference routes now require secure JWT
  credentials via `Depends(get_current_user)` (unauthorized requests are
  blocked with 401). The `/health` probe remains open for monitoring.

### `app/api/ws.py`
- **Section 6 (Heartbeat)** — The `/api/v1/stream` endpoint now answers
  `ping` (plain or `{"type": "ping"}`) with a `pong` echo so clients can
  monitor connection latency.
- **R-4.6.1 (Batching)** — The Redis→WebSocket distributor supports optional
  periodic message batching (`{"type": "telemetry_batch", "events": [...]}`),
  controlled by `WS_BROADCAST_BATCH_MS`. Default `0` preserves the legacy
  per-message broadcast behaviour (fully backwards compatible).

### `apps/core/api/asset.py` / `apps/core/api/alert.py`
- **R-4.2.1** — `limit` (default 100, max 100) and `offset` query parameters
  on `/api/v1/assets` and `/api/v1/alerts`; out-of-bounds values return the
  standard 422 validation envelope. Also migrated deprecated `regex=` → `pattern=`.

### `app/api/industrial.py` / `app/api/dashboard.py`
- **R-4.4.1** — All timestamp serialization switched from bare `.isoformat()`
  to `utc_iso()` (strict `YYYY-MM-DDTHH:mm:ssZ`).
- **Contract alignment** — `GET /api/v1/industrial/assets` now returns the
  frontend envelope `{"items": [...], "total_count": n, "critical_count": n}`;
  alarm resolution response includes `"status": "resolved"` (both matching the
  declared test contracts).

### Tests updated for the new contracts
- `tests/test_ai_proxy.py` — relay tests now authenticate with a signed JWT
  (lazily minted so per-session secret swaps keep working).
- `tests/smoke_tests.py` — login-without-body expectation corrected to 422 per
  the Section 2 contract matrix; WebSocket route check made functional
  (invalid token ⇒ close code 4001).
- `tests/test_auth.py` — error assertions aligned to the platform-standard
  flattened envelope produced by the global exception handler.

## 3. Verification

```
169 passed  (test_auth, smoke_tests, test_ai_proxy, test_assets,
             test_phase4_frontend_integration, test_stage2_auth, test_core,
             test_deps_stage0, test_contracts, test_phase2_backend_contracts,
             test_stage5_migration)
```

Runtime checks (uvicorn boot):
- `GET /health` → 200 healthy
- `GET /api/v1/assets/` without token → 401 standard envelope
- CORS preflight from `http://localhost:3000` → explicit method/header
  allow-lists, credentialed, origin echoed correctly
- Oversized AI Gateway payload → 413 `PAYLOAD_TOO_LARGE` envelope
- WS `/api/v1/stream` — invalid token rejected 4001; ping/pong heartbeat OK

Pre-existing failures in `tests/test_phase3_core.py` and `tests/test_users.py`
were confirmed present on the untouched upstream clone and are unrelated to
Phase 4 (they reference legacy exception-handler class names and a stub user
store that were changed in earlier phases).
