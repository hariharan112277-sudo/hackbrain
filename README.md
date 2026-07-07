# IOB Data Engine — Stage 1

**Industrial Data Acquisition & Simulation Setup** for the IOB
(Industrial Operational Brain) project.  Owned by **Member 2**.

A configuration-driven, multi-threaded IIoT data ingestion and
simulation pipeline that feeds the rest of the system (Member 1's
REST APIs, Member 3's AI/ML stack, Member 4's K8s deployment).

---

## 🎯 What this package does

| Layer | Module | Purpose |
| --- | --- | --- |
| Config | `src/config_loader.py` | YAML loader + legacy `machines.yaml`/`sensors.yaml` merge |
| Simulator | `src/simulator/device_profiles.py` | `TelemetryGenerator` (sinusoidal process variation + bounded noise) |
| Simulator | `src/simulator/core_simulator.py` | `IndustrialSimulator` — one thread per device, publishes JSON to MQTT |
| Ingestion | `src/ingestion/validator.py` | **Pydantic** schema enforcement (`TelemetryPayloadSchema`) |
| Ingestion | `src/ingestion/parser.py` | `NormalizationEngine` — UNS topic parsing, epoch → ISO 8601 UTC |
| Ingestion | `src/ingestion/mqtt_client.py` | `TelemetryIngestionWorker` — MQTT subscriber, drives the pipeline |
| Database | `src/database/telemetry_repository.py` | `TelemetryRepository` — `iob_normalized_telemetry` table + INSERT |
| Wiring | `src/integration_bridge.py` | Auto-discovers existing project root for legacy reuse |
| Entry | `main_stage1.py` | Boots all three layers with graceful shutdown |

**Strictly out of scope** (per spec):
- ❌ FastAPI endpoints, RBAC, auth (Member 1)
- ❌ Knowledge Graph, ML models (Member 3)
- ❌ K8s manifests, CI/CD (Member 4)

---

## 🗂️ Folder structure

```
iob_data_engine/
├── config/
│   ├── mqtt_broker.conf             # Mosquitto broker config
│   └── simulator_config.yaml        # YAML: version, broker, devices[]
├── src/
│   ├── __init__.py
│   ├── config_loader.py             # YAML loader + legacy merge
│   ├── integration_bridge.py        # Optional bridge to existing repo
│   ├── simulator/
│   │   ├── __init__.py
│   │   ├── device_profiles.py       # TelemetryGenerator
│   │   └── core_simulator.py        # IndustrialSimulator (threaded)
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── validator.py             # Pydantic TelemetryPayloadSchema
│   │   ├── parser.py                # NormalizationEngine (UNS parsing)
│   │   └── mqtt_client.py           # TelemetryIngestionWorker
│   └── database/
│       ├── __init__.py
│       └── telemetry_repository.py  # iob_normalized_telemetry
├── tests/
│   ├── __init__.py
│   ├── test_config_loader.py
│   ├── test_simulator.py
│   ├── test_ingestion.py
│   ├── test_database.py
│   └── test_e2e_pipeline.py
├── main_stage1.py                   # Orchestrator entry point
├── requirements.txt
└── README.md
```

---

## 📜 YAML contract (`config/simulator_config.yaml`)

```yaml
version: "1.0"
broker:
  host: "localhost"
  port: 1883
  keepalive: 60
  client_id: "iob_simulator_engine"
devices:
  - id: "DEV_CNC_001"
    name: "5-Axis CNC Milling Machine"
    type: "discrete"
    topic: "iob/uns/site_alpha/area_machining/cnc001/telemetry"
    update_interval_secs: 1.0
    metrics:
      - name: "spindle_speed_rpm"
        data_type: "float"
        min_val: 0.0
        max_val: 12000.0
        noise_amplitude: 50.0
database:
  dbname: "iob_db"
  user: "postgres"
  password: "postgres"
  host: "localhost"
  port: 5432
```

**Topic convention**: `iob/uns/<site>/<area>/<device_id>/telemetry`

**Wire payload format** (published by simulator):
```json
{
  "device_id": "DEV_CNC_001",
  "timestamp": 1700000000.123,
  "telemetry": {
    "spindle_speed_rpm": 8500.1234,
    "vibration_amplitude_g": 1.2
  }
}
```

**Normalized record** (stored in PG):
```json
{
  "device_id":     "DEV_CNC_001",
  "site_id":       "site_alpha",
  "area_id":       "area_machining",
  "timestamp_utc": "2024-01-01T00:00:00.123000+00:00",
  "metrics":       { ... }
}
```

---

## 🚀 Quickstart

### 1. Install dependencies

```bash
cd iob_data_engine
pip install -r requirements.txt
```

### 2. Start the broker and DB

```bash
# Mosquitto MQTT broker
docker run -d --name mosquitto \
  -p 1883:1883 \
  -v "$(pwd)/config/mqtt_broker.conf:/mosquitto/config/mosquitto.conf" \
  eclipse-mosquitto:2

# PostgreSQL with the schema from this Stage 1
docker run -d --name iob-postgres \
  -e POSTGRES_DB=iob_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:15
```

### 3. Run Stage 1

```bash
python main_stage1.py
```

Sample log output:
```
[IOB STAGE 1] Starting Industrial Operating Brain Infrastructure...
[INFO] iob.config_loader: Loaded config from .../config/simulator_config.yaml
       (version=1.0, devices=3)
[INFO] iob.repository: Telemetry table initialized (iob_normalized_telemetry)
[INFO] iob.ingestion.mqtt: Ingestion worker connected; subscribed to iob/uns/#
[INFO] iob.simulator: Started simulator thread for DEV_CNC_001 (...)
[INFO] iob.simulator: Started simulator thread for DEV_RE_002 (...)
[INFO] iob.simulator: Started simulator thread for DEV_HP_003 (...)
[IOB STAGE 1] Run loop active. Simulating and Ingesting IIoT stream data.
              Press Ctrl+C to terminate.
```

CLI flags:

```bash
python main_stage1.py --no-database    # simulator → MQTT → nowhere
python main_stage1.py --no-simulator   # ingestion worker only
python main_stage1.py --runtime 30     # bounded smoke test (auto-exit)
python main_stage1.py --log-level DEBUG
```

---

## 🧪 Tests

```bash
cd iob_data_engine
PYTHONPATH=. python -m pytest tests/ -v
# Or plain unittest:
PYTHONPATH=. python -m unittest discover -s tests -v
```

Coverage:

* `test_config_loader.py` — YAML loading, required keys, error paths
* `test_simulator.py` — TelemetryGenerator bounds/determinism;
  IndustrialSimulator thread spawn, MQTT publish format
* `test_ingestion.py` — Pydantic schema rejects bad payloads,
  NormalizationEngine extracts UNS components, worker stats
* `test_database.py` — Repository init_tables & save_telemetry
* `test_e2e_pipeline.py` — Full simulator → worker → repo path
  using mocked paho & DB

---

## 🔌 Integration with your existing repo

Drop this folder next to your existing `simulator/`, `ingestion/`,
`database/`, `integration/`.  Two automatic integration points:

### A. Reuse legacy `config/machines.yaml` + `config/sensors.yaml`

`ConfigLoader.load_with_legacy()` auto-detects those files at
`<project_root>/config/` and merges them into the Stage 1 device list
(idempotent — duplicate `id`s are skipped).  Pass `--project-root`
to `main_stage1.py` to point at the parent repo, or rely on the
auto-discovery in `src/integration_bridge.py`.

### B. Reuse existing PG connection wrapper

`src/integration_bridge.py:try_import_existing_postgres_connection()`
walks parent dirs looking for the existing project root and tries to
import `database.connection.PostgresConnection`.  If found, you can
swap Stage 1's wrapper:

```python
from src.integration_bridge import try_import_existing_postgres_connection
PostgresConnection = try_import_existing_postgres_connection()
```

---

## ✅ Validation checklist (from spec)

- [x] YAML config loads cleanly via `ConfigLoader.load_yaml()`
- [x] Pydantic rejects non-numeric / structurally invalid payloads
- [x] UNS topic parsing splits `site_id` and `area_id`
- [x] Native SQL `INSERT` into `iob_normalized_telemetry` works

---

## 🛡️ Risk mitigations (per spec)

| Risk | Mitigation |
| --- | --- |
| **#1** Schema drift between simulator & AI/API consumers | Strict Pydantic schema in `validator.py`; explicit `simulator_config.yaml` contract. Any change requires Team Checkpoint. |
| **#2** High ingestion latency under load | UNS topic fan-in via single `iob/uns/#` subscription; per-message INSERT with `commit()`. For higher throughput, swap `TelemetryRepository` to use batched `executemany` (a drop-in replacement). |

---

## 📜 Team checkpoints

* **Checkpoint 1 (Member 1)** — `iob_normalized_telemetry` schema
  (see `telemetry_repository.py:INIT_TABLE_SQL`).  Confirm column
  names + types align with Member 1's REST querying layer.
* **Checkpoint 2 (Member 3)** — Output JSON shape of
  `NormalizationEngine.normalize()` (see `parser.py`).  Confirm it
  matches Graph RAG / predictive training expectations.
