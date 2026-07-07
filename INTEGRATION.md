# Integration Guide — `iob_data_engine` ↔ your existing IOB repo

This guide explains how to drop the **`iob_data_engine/`** package into
your existing repository layout (`hackbrain/`) so Stage 1 wires up with
the modules you already have.

---

## TL;DR

```bash
# 1. From your hackbrain/ root:
cp -r iob_data_engine/ ./iob_data_engine/

# 2. Install the Stage 1 deps alongside your existing ones:
pip install -r iob_data_engine/requirements.txt

# 3. Run Stage 1 (auto-discovers your existing project root):
python iob_data_engine/main_stage1.py
```

---

## What gets reused automatically

### 1. Legacy `config/machines.yaml` + `config/sensors.yaml`

`src/config_loader.py:ConfigLoader.load_with_legacy()` reads your
existing YAML files at `<project_root>/config/` and appends any new
devices to the Stage 1 device list (idempotent — duplicates skipped).

Run with the auto-discovery flag:

```bash
python iob_data_engine/main_stage1.py --project-root /path/to/hackbrain
```

Or skip the flag and let `src/integration_bridge.py` find the project
root automatically by walking parent directories looking for
`simulator/` + `ingestion/` folders.

### 2. Existing `database.connection.PostgresConnection`

The integration bridge in `src/integration_bridge.py` can import your
existing PG wrapper:

```python
from src.integration_bridge import try_import_existing_postgres_connection
ExistingPG = try_import_existing_postgres_connection()
if ExistingPG:
    print("Using your existing database.connection.PostgresConnection")
```

### 3. Existing topic conventions (`config/topics.yaml`)

Your existing `config/topics.yaml` can override the Stage 1 topic
prefixes.  In `main_stage1.py` after loading the config:

```python
import yaml
from pathlib import Path
legacy_topics = yaml.safe_load(Path("../config/topics.yaml").read_text())
config["broker"].update(legacy_topics.get("broker", {}))
```

---

## Boundaries preserved (per spec)

* ❌ Does **NOT** touch Member 1 territory (FastAPI, RBAC).
* ❌ Does **NOT** touch Member 3 territory (Knowledge Graph, ML).
* ❌ Does **NOT** touch Member 4 territory (K8s, CI/CD).
* ✅ Provides normalized telemetry in `iob_normalized_telemetry`
  for Members 1 & 3 to consume.

---

## Verification checklist

1. ✅ `PYTHONPATH=. python -m pytest iob_data_engine/tests/` → all pass
2. ✅ `python iob_data_engine/main_stage1.py --help` → CLI works
3. ✅ Start Mosquitto + PG, then run `python main_stage1.py`
4. ✅ Query PG: `SELECT count(*), device_id FROM iob_normalized_telemetry GROUP BY device_id;`
