# Industrial Operating Brain (IOB) — Phase 3

**Data Generation & Digital Twin Simulation Engine**
Version `1.0.0-SIM` · Operational Technology (OT) Emulation Framework

Standards alignment: **ISA-95** (Part 1 & 2), **IEC 62541** (OPC-UA information
models), **ISO/IEC 20922** (MQTT 5.0).

This engine emulates a multi-asset smart factory. Each machine is a
state-machine-driven digital twin that synthesises physically plausible
telemetry from its instrumented sensors and publishes it to an EMQX MQTT bus
for downstream consumers (the Phase 1/Phase 2 ingestion pipeline and the
`ethack` Next.js digital-twin dashboard).

---

## Architecture

```
CFG_YML ──▶ ConfigManager ──▶ FactorySimulator ──▶ MachineInstance ──▶ SensorSimulator
                                                                    │
                                                          PhysicsWaveformEngine
                                                                    │
                                                          TelemetryBuilder
                                                                    │
                                                          MqttPublisherEngine ──▶ EMQX
```

| Module | Responsibility |
| ------ | -------------- |
| `simulator/config.py` | `ConfigManager` — loads & validates the declarative YAML configuration. |
| `simulator/constants.py` | Machine states (ISA-95) and sensor data-quality flags. |
| `simulator/generator.py` | `PhysicsWaveformEngine` — sinusoidal drift, Box-Muller noise, thermal inertia, limit clamping. |
| `simulator/sensor.py` | `SensorSimulator` — per-instrument twin with drift, spontaneous link drops and sample-frequency gating. |
| `simulator/machine.py` | `MachineInstance` — state-machine asset with autonomous lifecycle transitions. |
| `simulator/telemetry.py` | `TelemetryBuilder` — ISA-95 / Phase 1 compliant JSON envelope. |
| `simulator/publisher.py` | `MqttPublisherEngine` — MQTT 5.0 publisher with graceful OFFLINE degradation. |
| `simulator/factory.py` | `FactorySimulatorOrchestrator` — main 10 ms evaluation loop. |

---

## Project layout

```
iob-phase3/
├── simulator/            # Emulation core (see table above)
│   ├── __init__.py
│   ├── config.py
│   ├── constants.py
│   ├── factory.py        # entry point (cd simulator && python factory.py)
│   ├── generator.py
│   ├── machine.py
│   ├── publisher.py
│   ├── sensor.py
│   ├── telemetry.py
│   └── utils.py
├── config/               # Declarative configuration
│   ├── machines.yaml     # enterprise / site / plant + machine definitions
│   ├── sensors.yaml      # sensor templates per machine type
│   └── topics.yaml       # MQTT / EMQX connection settings
├── logs/                 # runtime logs (git-ignored)
├── sample_data/          # sample payloads + generator
│   ├── sample_telemetry.json    # canonical single-envelope example (spec 5.1)
│   ├── sample.jsonl             # generated telemetry stream
│   └── generate_sample.py
├── tests/
│   ├── conftest.py
│   ├── test_simulation_curves.py
│   └── test_operational_scenarios.py
├── requirements.txt
└── README.md
```

---

## Installation

```bash
cd iob-phase3
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
```

---

## Configuration

All behaviour is data-driven from `config/*.yaml`.

- **`machines.yaml`** — `factory_metadata` (enterprise/site/plant) and the list
  of machines (id, name, type, manufacturer, production line).
- **`sensors.yaml`** — `sensor_templates` keyed by machine `type`. Each template
  declares range, unit, sample frequency, noise variance and failure probability.
- **`topics.yaml`** — `mqtt_settings`: broker host/port, keep-alive, client id,
  QoS for telemetry vs alarms, and the root namespace.

Override the configuration directory at runtime with the `IOB_CONFIG_DIR`
environment variable.

---

## Running

### Live (with an EMQX / MQTT broker)

```bash
cd simulator
pip install paho-mqtt pyyaml
python factory.py
```

(The engine can also be launched from the repo root via
`python simulator/factory.py`.)

It connects to the broker defined in `config/topics.yaml`, runs the emulation
loop, and publishes telemetry under topics such as:

```
gmc/aus/asy/wld01/rob01/telemetry/temperature
gmc/aus/asy/wld01/rob01/telemetry/current
gmc/aus/asy/wld01/cnc01/telemetry/speed
```

Stop with `Ctrl-C` for a graceful shutdown.

### Smoke test without a broker (OFFLINE mode)

The engine degrades gracefully when `paho-mqtt` is unavailable or the broker is
unreachable — telemetry keeps flowing to an in-process side channel instead of
the bus:

```bash
IOB_MAX_DURATION=6 IOB_LOG_OFFLINE=1 python simulator/factory.py
```

### Static sample data

```bash
python sample_data/generate_sample.py --count 200
# writes sample_data/sample.jsonl  (one envelope per line, JSON)
```

---

## Telemetry envelope

A canonical, hand-verified example lives at
[`sample_data/sample_telemetry.json`](sample_data/sample_telemetry.json); a
larger generated stream is in [`sample_data/sample.jsonl`](sample_data/sample.jsonl)
(produced by `python sample_data/generate_sample.py`).

```json
{
  "timestamp": "2026-07-02T12:00:05.104211Z",
  "asset_id": "GMC_AUS_ASY_WLD01_ROB01_WRI05_TE01",
  "machine_id": "GMC_AUS_ASY_WLD01_ROB01",
  "sensor_id": "GMC_AUS_ASY_WLD01_ROB01_WRI05_TE01",
  "topic": "gmc/aus/asy/wld01/rob01/telemetry/temperature",
  "measurement": "axis_5_wrist_temperature",
  "value": 62.3412,
  "unit": "CELSIUS",
  "quality": "GOOD",
  "sequence_number": 402,
  "gateway_id": "AUS_ASY_GW01",
  "site_id": "AUS",
  "plant_id": "ASY",
  "line_id": "WLD01",
  "processing_status": "RAW",
  "metadata": {
    "machine_type": "ASSEMBLY_ROBOT",
    "operating_hours": 12.4105,
    "machine_state": "RUNNING"
  }
}
```

---

## Testing

```bash
pytest -q
```

`tests/test_simulation_curves.py` validates the physics curves, sensor sampling
intervals, machine lifecycle transitions, telemetry envelope structure, config
loading, and end-to-end offline publishing.

- `tests/test_operational_scenarios.py` — the three operational scenarios from
  spec section 6 (see below), mapped to their downstream consumers.

## Operational simulation scenarios (spec section 6)

The framework is verified against the canonical emulation matrix. Each scenario
exercises the full stack (machine → sensor → generator → telemetry) and asserts
the mathematical signature a downstream consumer depends on:

| Scenario | Emulated behaviour | Signature | Downstream consumer |
| -------- | ------------------ | --------- | ------------------- |
| **Normal Steady State** | Sinusoidal oscillation + low Gaussian noise | Values oscillate around the base operating point, all `GOOD`, within range | **Member 1** (Backend ingestion) |
| **Asset Thermal Failure** | Progressive mechanical failure | Value steps past `max_limit`; status flips to `LIMIT_CLAMPED` | **Member 3** (AI engine / predictive health) |
| **Emergency Stop (E-Stop)** | Immediate state step response | Values drop instantly to zero, or to the sensor's ambient reference base point | **Member 4** (Frontend hazard alerting) |

## Scalability & extensibility (spec section 7.2)

Adding capacity is fully declarative — no engine code changes. Append a machine
to `config/machines.yaml` and (if it is a new type) its sensor template to
`config/sensors.yaml`; the orchestrator auto-detects it, binds child sensors
from the template matrix, spawns its runtime loop and builds its Unified
Namespace MQTT topic paths.

A third asset, `GMC_AUS_ASY_WLD01_PMP02` (**INDUSTRIAL_PUMP**), is already wired
in out of the box to demonstrate this.

```yaml
# config/machines.yaml  (append)
- machine_id: "GMC_AUS_ASY_WLD01_PMP02"
  name: "Cooling Loop Recirculation Pump"
  type: "INDUSTRIAL_PUMP"
  production_line: "WLD01"
```

---


## Connecting to the `ethack` dashboard

The `ethack` repository (Next.js + React) is the **front-end** digital-twin
dashboard (`DigitalTwinView`, telemetry/alert/prediction services). This
simulator is the **back-end** data source. To wire them together:

1. Run an MQTT broker (EMQX) reachable at the host/port in `config/topics.yaml`.
2. Start this engine: `python simulator/factory.py`.
3. Point the dashboard's `NEXT_PUBLIC_MQTT_*` settings at the same broker so
   `src/services/*` can subscribe to `gmc/aus/asy/#`.

The dashboard then renders live twin state, alerts, and SHAP explainability
straight from this engine's telemetry stream.
