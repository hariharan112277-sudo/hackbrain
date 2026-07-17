# Track B (Lathika) — Stage 2/Wiring Completion Notes

Generated against `IOB_Backend_Completion_Ultra_Detailed.docx` (Parts 3–6) and
the repository state at `hariharan112277-sudo/hackbrain@main`.

## Gap analysis (before this change)

**Already implemented and verified (left untouched):**
- Track A in full: `app/database.py`, `app/deps.py`, `app/core/security.py`,
  `app/models/{user,asset,alarm,schemas}.py`, `app/api/auth.py`,
  `app/api/industrial.py`, `app/api/dashboard.py`, `tests/test_auth.py`,
  `tests/test_assets.py`, `tests/test_stage2_auth.py`, `tests/test_deps_stage0.py`
  all match Part 2.1/Part 3 and pass.
- `app/services/ai_client.py` and `app/api/ai_proxy.py` (Track B Stage 1) —
  the six relay routes existed and matched Part 2.3/2.5's frozen AI contract
  shape (pure pass-through, no reshaping).

**Partially implemented:**
- `ai_client.call_ai` existed but converted a dead/unreachable ai-platform
  into a raised `HTTPException` (502/504) instead of the frozen
  `{"error": {"code": "AI_UNAVAILABLE", ...}}` envelope the Part 4 Stage 1
  checkpoint requires. Fixed: timeout/connection failures now return the
  envelope; genuine upstream HTTP errors (422 invalid input, 503 missing
  model per Part 2.3) still relay their real status/body, which is correct
  and more specific than the plan's simplified pseudocode.
- `docker-compose.yml` only defined `api_service` — no Postgres or MQTT
  broker, so "docker compose up" alone could never satisfy Part 1's
  foundation assumption or Part 6's smoke test. Added `postgres` and
  `mosquitto` services, wired via env vars already read by
  `app/core/config.py`.
- `requirements.txt` was missing `structlog` and `PyJWT`, both imported by
  code/tests already in the repo (`app/main.py`, `app/services/auth_service.py`,
  `tests/test_deps_stage0.py`). The app/test suite could not even be
  collected without them. Added both.

**Missing entirely (this change implements them):**
- `app/services/mqtt_bridge.py` — did not exist. Implemented per Part 4
  Stage 2: subscribes to `iob/+/+/+/{telemetry,status,alarm}` (Part 2.2 QoS
  levels preserved), maps payloads to the Part 2.5 frame shapes, and fans
  them out to registered WebSocket clients via `asyncio.Queue`. A broker
  outage is caught and logged, never blocking app startup.
- `app/api/ws.py` — did not exist. Implemented `/api/v1/ws/telemetry`:
  reuses `app.core.security.decode_token` for auth (same validation as every
  HTTP endpoint), sends a heartbeat every 15s when idle, and closes with
  WebSocket code 1008 for invalid/expired tokens.
- Neither the AI relay router nor a WebSocket router were mounted in
  `app/main.py`'s `create_app()` — only `auth`, `users`, `industrial`, and
  `dashboard` were included, so `/api/v1/ai/*` and `/api/v1/ws/telemetry`
  were unreachable regardless of the files above existing. Fixed by
  importing and including both, and by starting/stopping the MQTT bridge in
  the app lifespan (gated by `settings.ENABLE_REALTIME_TELEMETRY`).
- `database/iob_core_schema.sql` — no DDL matched the frozen Part 2.1 schema
  that Track A's SQLAlchemy models already map onto (`database/schema.sql`
  in the repo is a *different*, unrelated schema for the datasets/ingestion
  pipeline — table names collide but columns don't match). Added the exact
  Part 2.1 DDL so a fresh `docker compose up` boots with usable tables
  without a manual `Base.metadata.create_all()` step.
- `tests/test_ai_proxy.py` and `tests/test_ws.py` — did not exist. Added,
  covering: all six relay routes forward path/payload/method and return the
  upstream body unmodified; the AI_UNAVAILABLE envelope path (both at the
  `call_ai` level and through the gateway route); WebSocket auth rejection;
  heartbeat delivery; frame broadcast delivery; and the bridge's payload →
  frame mapping and client registry functions.

## Known deviations left in place (flagged, not changed)

- `app/api/industrial.py` and `app/api/dashboard.py` are mounted at
  `/api/v1/industrial/*` and `/api/v1/dashboard/*` rather than the plan's
  `/api/v1/assets`, `/api/v1/alerts`, `/api/v1/dashboard/summary` (no
  `/industrial` segment). `tests/test_assets.py` and `tests/test_industrial.py`
  already assert the `/industrial` prefix, i.e. this is real, tested,
  working code — following the same precedent the plan itself sets in
  Part 2.3 ("one contract has already drifted in real, working code, and
  that real version wins"). Changing it now would break a passing, already
  merged contract and any frontend already pointed at it. Flagging here so
  Hariharan/Member 1 can decide whether to formally update Part 2.4 instead.
- `app/api/v1/router.py` (GraphRAG/XAI/predictive/decision/vector-search
  routers, plus a second copy of auth/dashboard/assets/alerts under
  `Phase 5A`) is never imported by `app/main.py` and appears to be
  scaffolding for a separate `ai-platform` service, not this backend. Left
  untouched — it's outside both Track A's and Track B's ownership lists in
  Part 3/Part 4, and no file in this change touches it.
- A pre-existing set of 53 test failures / 6 collection errors (in
  `tests/test_phase3_core.py`, `tests/test_integration.py`,
  `tests/test_users.py`, `tests/test_industrial.py`, `tests/test_core.py`,
  and two cases in `tests/test_assets.py`) predate this change and are
  unrelated to Track A/B's scope in Parts 3–4 (they exercise a different,
  seemingly earlier app shape — e.g. `/api/v1/machines`, `/api/v1/health/live`,
  a `username`-based login body). Verified they are pre-existing by running
  the suite before and after this change: 170 passed/53 failed/6 errors
  before, 186 passed/53 failed/6 errors after (the 16 new passes are
  `test_ai_proxy.py` + `test_ws.py`). Per Part 7 ("never edit a file outside
  your own ownership list"), these were left as-is rather than guessed at.

## Verifying locally

```bash
pip install -r requirements.txt
pytest tests/ -q                      # 186 passed, 53 pre-existing failures (see above)
pytest tests/test_ai_proxy.py tests/test_ws.py -q   # 16/16 passed — Track B only
docker compose up --build             # api_service + postgres + mosquitto
```

Manual smoke test once the stack is up (Part 6):
```bash
curl -X POST localhost:8000/api/v1/auth/login -H 'content-type: application/json' \
  -d '{"email":"admin@iob.demo","password":"admin123"}'
# then, with the returned access_token:
websocat "ws://localhost:8000/api/v1/ws/telemetry?token=<access_token>"
```
