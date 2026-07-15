# Track A — Stage 1 (Database Layer) — Delivery Notes

**Owner:** Hariharan (Track A) · **Scope:** `app/database.py`, `app/deps.py`, `app/models/*`
**Status:** ✅ Implemented, integrated with existing repo wiring, and verified.

---

## 1. What this ZIP contains (extract over the repo root)

```
track_a_stage1_database_layer/
├── app/
│   ├── database.py          # [NEW]  Engine, SessionLocal, Base, get_db()  (spec-verbatim)
│   ├── config.py            # [NEW]  Settings alias shim (integration glue — see §3)
│   ├── deps.py              # [NEW]  Canonical get_db import point + DBSession alias
│   └── models/
│       ├── __init__.py      # [NEW]  Registers all models on Base.metadata (anti-circular)
│       ├── user.py          # [NEW]  users                    (spec-verbatim)
│       ├── asset.py         # [NEW]  assets, sensors, telemetry, events, maintenance_logs
│       ├── alarm.py         # [NEW]  alarms                   (spec-verbatim)
│       └── schemas.py       # [NEW]  Pydantic DTOs mirroring the frozen columns 1:1
├── requirements.txt         # [EDIT] 1 additive line: SQLAlchemy>=2.0.0,<3.0
├── .env.example             # [EDIT] additive DATABASE_URL documentation block
├── verify_track_a_stage1.py # [BONUS] Offline verification harness (all 6 checks)
└── TRACK_A_STAGE1_NOTES.md  # this file
```

## 2. Frozen schema contract — implemented exactly (no renames, no extras)

| Table | PK | Notes |
|---|---|---|
| `users` | `user_id` UUID, `server_default=gen_random_uuid()` | `email` UNIQUE, `role` default `viewer` |
| `assets` | `asset_id` String(20) | `machine_id` UNIQUE; relationships to all child tables |
| `sensors` | `sensor_id` String(20) | FK `asset_id → assets.asset_id` |
| `telemetry` | `id` BigInteger autoincrement (→ `BIGSERIAL` in PG) | FK + 7 NUMERIC metric columns |
| `events` | `event_id` BigInteger autoincrement | FK |
| `maintenance_logs` | `id` BigInteger autoincrement | FK |
| `alarms` | `alarm_id` String(30) | FK, `resolved` Boolean default False |

## 3. Integration decisions (why 3 files exist beyond the spec's code blocks)

1. **`app/config.py` (shim):** the spec mandates `from app.config import settings` inside
   `app/database.py`, but the repo's canonical settings live in `app.core.config`
   (with `DATABASE_URL` already defined and required). The shim re-exports that **same
   cached `Settings` object**, so the spec file stays byte-verbatim AND the existing
   Phase-5 wiring (`app/main.py`, `app/core/*`) keeps working unchanged. One source
   of truth — no duplicated config.
2. **`app/models/__init__.py`:** imports every model so all tables register on
   `Base.metadata` and every `relationship("...")`/back_populates pair resolves
   regardless of import order (Checkpoint 1, item 2 — no circular traps).
3. **`app/deps.py`:** re-exports `get_db` so routers use a stable path —
   `from app.deps import get_db` — decoupled from engine internals.
   `app/core/dependencies.py` (another track) was **not** touched.

**Shared-file edits were strictly additive** (proven by `git diff`): one dependency
line in `requirements.txt` (SQLAlchemy was missing — nothing works without it) and a
documenting `DATABASE_URL` block in `.env.example`.

## 4. Verification results (executed in a clean sandbox against this repo)

| # | Check | Result |
|---|---|---|
| 1 | Engine builds from `settings.DATABASE_URL` with real `psycopg2` dialect | ✅ `Engine(postgresql+psycopg2://…)` |
| 2 | All 7 models import; tables registered on `Base.metadata`; `configure_mappers()` resolves every relationship | ✅ |
| 2b | All 5 child `asset_id` FKs → `assets.asset_id` | ✅ |
| 3 | DDL for all 7 tables compiles against the **real PostgreSQL dialect**; contract tokens present: `gen_random_uuid()`, `DEFAULT now()`, `DEFAULT 'viewer'`, `UNIQUE (email)`, `UNIQUE (machine_id)`, `UUID`, `BIGSERIAL`, `NUMERIC`, `BOOLEAN`, `TIMESTAMP WITH TIME ZONE` | ✅ |
| 4 | `get_db` yields a live `Session` and the `finally: db.close()` block verifiably executes | ✅ |
| 5 | `app.config` shim aliases the same settings object; `app.deps.get_db is app.database.get_db`; ORM→Pydantic round-trip works | ✅ |
| 6 | Regression: existing app boot | ⚠️ see §5 |

`git status` confirms: only the 8 new Track-A files + the 2 additive shared edits.
**No Track-B or external schema files were modified.**

## 5. ⚠️ One heads-up for Track B (pre-existing bug, NOT from this change)

`app/schemas/auth.py` line **81** contains a syntax error that already exists in the
repo and blocks `app.main` from booting:

```python
if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for v):   # ← malformed
# fix:   any(c in "...chars..." for c in v)
```

This file belongs to another track, so per ownership rules it was **left untouched**.
It does **not** affect Track A — `app.database`, `app.models`, `app.deps` and the
Checkpoint 1 command run without importing `app.schemas`.

*(Also noted for the team's requirements owner: `structlog` and `PyJWT` are imported
by existing Phase-5 code but absent from `requirements.txt` — pre-existing gaps.)*

## 6. Running Checkpoint 1 on your machine (live Postgres)

```bash
# 1. Unzip over the repo root   →   unzip -o track_a_stage1_database_layer.zip
# 2. Install deps
pip install -r requirements.txt
# 3. Create your .env (DATABASE_URL now documented in .env.example)
cp .env.example .env      # then set SECRET_KEY (>=32 chars) and DATABASE_URL
#    e.g. DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/iob
# 4. Checkpoint 1 — exact spec command:
python -c "from app.database import engine; print(engine.connect())"
```

Expected output against a live Postgres:

```
<sqlalchemy.engine.base.Connection object at 0x...>
```

Optional deeper checks:

```bash
python verify_track_a_stage1.py          # full offline suite (checks 1–6)
# Create the tables in your dev database (server defaults fire):
python -c "import app.models; from app.database import engine, Base; Base.metadata.create_all(engine); print('tables created:', sorted(Base.metadata.tables))"
```
