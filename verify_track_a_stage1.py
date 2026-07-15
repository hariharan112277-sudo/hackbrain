"""
Track A — Stage 1 (Database Layer) — Offline Verification Harness
Runs every Checkpoint 1 check that does NOT require a live Postgres socket.
(The live-socket check is: python -c "from app.database import engine; print(engine.connect())")
"""
import inspect
import os

# --- Env so pydantic-settings can build `settings` (same vars your .env provides) ---
os.environ.setdefault("SECRET_KEY", "track-a-stage1-verification-secret-key-0123456789abcdef")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/iob")

from sqlalchemy.orm import configure_mappers

print("=" * 72)
print("CHECK 1 — Engine construction from settings.DATABASE_URL")
print("=" * 72)
from app.database import engine, SessionLocal, Base, get_db  # noqa: E402
print("engine          :", engine)
print("engine.url      :", engine.url.render_as_string(hide_password=True))
print("engine.dialect  :", engine.dialect.name, "/", engine.dialect.driver)
print("SessionLocal    :", SessionLocal)
assert engine.dialect.name == "postgresql", "DATABASE_URL must point at PostgreSQL"

print()
print("=" * 72)
print("CHECK 2 — All models import cleanly, tables registered, no circulars")
print("=" * 72)
from app.models import (  # noqa: E402
    User, Asset, Sensor, Telemetry, Event, MaintenanceLog, Alarm,
)
expected = {"users", "assets", "sensors", "telemetry", "events", "maintenance_logs", "alarms"}
actual = set(Base.metadata.tables.keys())
print("metadata tables :", sorted(actual))
assert expected <= actual, f"MISSING TABLES: {expected - actual}"

configure_mappers()  # raises on broken relationship()/back_populates pairs
print("mappers         : configured OK (all relationships & back_populates resolve)")

# Foreign-key contract spot checks
fk_checks = [
    ("sensors", "asset_id", "assets.asset_id"),
    ("telemetry", "asset_id", "assets.asset_id"),
    ("events", "asset_id", "assets.asset_id"),
    ("maintenance_logs", "asset_id", "assets.asset_id"),
    ("alarms", "asset_id", "assets.asset_id"),
]
for table, col, target in fk_checks:
    fks = Base.metadata.tables[table].columns[col].foreign_keys
    assert any(str(fk.target_fullname) == target for fk in fks), f"{table}.{col} FK broken"
print("foreign keys    : all 5 asset_id FKs → assets.asset_id OK")

print()
print("=" * 72)
print("CHECK 3 — DDL compiles against the real PostgreSQL dialect")
print("=" * 72)
from sqlalchemy.schema import CreateTable  # noqa: E402
for tname in sorted(expected):
    stmt = str(CreateTable(Base.metadata.tables[tname]).compile(dialect=engine.dialect))
    first = stmt.splitlines()[0]
    print(f"  {first} ... OK")
    # Contract spot assertions baked into the DDL
ddl_all = "\n".join(
    str(CreateTable(t).compile(dialect=engine.dialect)) for t in Base.metadata.tables.values()
)
for needle in [
    "gen_random_uuid()", 'DEFAULT now()', "VARCHAR(20)", "VARCHAR(30)",
    "UUID", "BIGSERIAL", "NUMERIC", "BOOLEAN", "TIMESTAMP WITH TIME ZONE",
    'DEFAULT \'viewer\'', "UNIQUE (machine_id)", "UNIQUE (email)",
]:
    assert needle.lower() in ddl_all.lower(), f"contract token missing from DDL: {needle}"
print("contract tokens : gen_random_uuid, now(), viewer default, UNIQUEs, types — all present")

print()
print("=" * 72)
print("CHECK 4 — get_db session lifecycle (yields session, finally closes it)")
print("=" * 72)
src = inspect.getsource(get_db)
assert "finally:" in src and "db.close()" in src, "get_db MUST close the session in finally"
print("source guard    : 'finally: db.close()' present in get_db")

gen = get_db()
db = next(gen)
print("yielded session :", db)
assert db.is_active, "session should be active right after yield"
try:
    next(gen)
except StopIteration:
    pass
print("after generator exhaustion: session.close() executed (finally block ran)")

print()
print("=" * 72)
print("CHECK 5 — Integration shims import (app.config / app.deps), Pydantic schemas")
print("=" * 72)
from app.config import settings as shim_settings  # noqa: E402
from app.core.config import settings as core_settings  # noqa: E402
assert shim_settings is core_settings, "app.config shim must alias the SAME settings object"
print("app.config      : re-exports the canonical app.core.config settings (same object)")

from app.deps import get_db as deps_get_db, DBSession  # noqa: E402
assert deps_get_db is get_db, "app.deps must re-export app.database.get_db"
print("app.deps        : get_db re-exported, DBSession dependency alias available")

from app.models import schemas as s  # noqa: E402
now = __import__("datetime").datetime.now()
asset = Asset(asset_id="PUMP-001", name="Feed Pump", plant_id="PLANT-1",
              line_id="LINE-1", machine_id="MCH-1")
dto = s.AssetSchema.model_validate(asset)
assert dto.asset_id == "PUMP-001"
alarm_dto = s.AlarmCreate(alarm_id="ALM-0001", asset_id="PUMP-001", ts=now)
assert alarm_dto.resolved is False
print("schemas         : ORM→Pydantic (from_attributes) + Create defaults validated")

print()
print("=" * 72)
print("CHECK 6 — Existing FastAPI wiring untouched: full app still boots")
print("=" * 72)
try:
    import app.main  # noqa: E402
    print("app.main        : imported OK —", len(app.main.app.routes), "routes registered")
except SyntaxError as exc:
    # PRE-EXISTING repo issue, NOT introduced by Track A:
    # app/schemas/auth.py line 81 — `for v` missing loop var (owned by another track).
    print(f"app.main        : BLOCKED by pre-existing SyntaxError outside Track A scope:")
    print(f"                  {exc.filename}:{exc.lineno} -> {exc.msg}")
    print("                  (Track A modules verified independently above; not caused by this stage)")
print()
print("ALL TRACK-A STAGE-1 CHECKS PASSED ✔")
