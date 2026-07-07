# JSON Schema Contract Validation Audit

**Stage:** 2 — Contract Validation, Alignment & Audit
**Owner:** Member 2 (Industrial Operating Brain — Data Foundation)
**Document ID:** `JSON-SCHEMA-CONTRACT-VAL-v1.0`
**Standards Alignment:** RFC 8259 (JSON), IETF JSON-Schema draft 2020-12, ISA-95 Part 2, ISO 8601
**Audit Date:** 2026-07-07 (UTC)
**Contract Baseline:** Canonical Stage 1 generation (`iob_data_engine` / `src/` + `config/simulator_config.yaml`)

---

## 1. Purpose & Scope

This document defines and validates the semantic data models for all edge-to-cloud payloads passing through the IOB ingestion pipeline. It establishes the authoritative, version-controlled JSON contracts for Telemetry, Alarms, Machine State, and Heartbeat envelopes, and verifies that their data types and structures are precisely aligned end-to-end from the industrial edge asset through the Normalizer into PostgreSQL storage and downstream consumption (Member 1 APIs, Member 3 AI datasets, Member 4 Dashboards).

**In Scope (Member 2 Audit Boundary):** Telemetry, Alarm, Machine-State, and Heartbeat JSON payload schemas; timestamp standardisation; units compliance.
**Out of Scope:** Member 1 business logic; Member 3 ML/graph architecture (read-only audit — no code/schema mutation).

---

## 2. Payload Schema Audits

### 2.1. Telemetry Payload Schema

The canonical telemetry envelope emitted by the simulator (`src/simulator/core_simulator.py`) and enforced at the ingestion boundary (`src/ingestion/validator.py :: TelemetryPayloadSchema`) is defined as:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "device_id": { "type": "string" },
    "timestamp": { "type": "number", "description": "Epoch timestamp (Seconds.Milliseconds)" },
    "telemetry": {
      "type": "object",
      "properties": {
        "spindle_speed_rpm": { "type": "number", "minimum": 0, "maximum": 15000 },
        "vibration_amplitude_g": { "type": "number", "minimum": 0, "maximum": 10 }
      },
      "required": ["spindle_speed_rpm", "vibration_amplitude_g"]
    }
  },
  "required": ["device_id", "timestamp", "telemetry"]
}
```

**Audit verification:**
- `device_id` (string) ↔ canonical topic leaf and `iob_normalized_telemetry.device_id` (VARCHAR). ✅
- `timestamp` (number, epoch float) ↔ `src/ingestion/parser.py` consumes `timestamp: float` and converts to `timestamp_utc`. ✅
- `telemetry` object with `spindle_speed_rpm` (0–15000) and `vibration_amplitude_g` (0–10) ↔ `config/simulator_config.yaml` metric families. ✅ Bounds are enforced by the Normalizer/quality-checker range guards.

### 2.2. Alarm Payload Schema

```json
{
  "type": "object",
  "properties": {
    "device_id": { "type": "string" },
    "timestamp": { "type": "number" },
    "alarm_code": { "type": "string" },
    "severity": { "type": "string", "enum": ["INFO", "WARNING", "CRITICAL"] },
    "message": { "type": "string" }
  },
  "required": ["device_id", "timestamp", "alarm_code", "severity", "message"]
}
```

**Audit verification:** The edge alarm envelope is a self-contained, strongly-typed contract. `severity` is constrained to the closed set `{INFO, WARNING, CRITICAL}`, preventing free-text severity drift. The subscribing alarm consumer (`ingestion/config/topics.yaml` → `gmc/aus/asy/+/+/alerts/+`, or the canonical `iob/uns/#` bus) receives a deterministic structure. The `alarm_code` string permits stable, versioned fault cataloguing.

### 2.3. Machine State Payload Schema

```json
{
  "type": "object",
  "properties": {
    "device_id": { "type": "string" },
    "timestamp": { "type": "number" },
    "current_state": { "type": "string", "enum": ["IDLE", "RUNNING", "MAINTENANCE", "FAULTED"] }
  },
  "required": ["device_id", "timestamp", "current_state"]
}
```

**Audit verification:** `current_state` is bound to the closed ISA-88 equipment-state set `{IDLE, RUNNING, MAINTENANCE, FAULTED}`. This maps cleanly to the retained state envelope consumed by Member 4 dashboards and the Member 1 state registry. No out-of-enum states are permitted.

### 2.4. Heartbeat Payload Schema

```json
{
  "type": "object",
  "properties": {
    "device_id": { "type": "string" },
    "timestamp": { "type": "number" },
    "status": { "type": "string", "enum": ["UP"] }
  },
  "required": ["device_id", "timestamp", "status"]
}
```

**Audit verification:** The heartbeat is a minimal liveness contract. `status` is pinned to the singleton enum `{UP}` (extensible to `DEGRADED`/`DOWN` in a future schema version). It enables Member 4 watchdog visualisation and Member 1 gateway health checks without per-tick telemetry overhead.

---

## 3. Structural Constraints & Datatype Verification

- **Timestamp Standard:** Edge telemetry utilizes high-precision float UNIX Epoch timestamps (`float64`). The Normalizer converts this to strict ISO 8601 format (`YYYY-MM-DDTHH:MM:SS.ffffffZ`) before DB persistence.
  - *Evidence:* `src/ingestion/parser.py :: NormalizationEngine.normalize()` → `datetime.datetime.fromtimestamp(parsed_data.timestamp, tz=datetime.timezone.utc).isoformat()` yields a UTC, timezone-qualified ISO-8601 string. This directly satisfies **Risk 2 (Timezone Misalignment)** mitigation in the Stage 2 charter.
- **Units Compliance:** Metric units are strictly tied to SI definitions or global standard industry parameters (RPM, G-force, Bar).
  - *Evidence:* `config/simulator_config.yaml` and `config/sensors.yaml` declare units per metric; `ingestion/normalizer.py` (`EngineeringUnitNormalizer`) standardises TEMPERATURE→CELSIUS, PRESSURE→BAR, SPEED→RPM. No ambiguous or non-standard unit strings are admitted into the canonical store.
- **Identifier Integrity:** `device_id` is a stable string primary correlation key carried identically across the wire envelope, the UNS topic leaf, and the `iob_normalized_telemetry.device_id` column — guaranteeing referential traceability without foreign-key coupling (see `database_schema_validation.md`).

**Verdict:** **COMPLIANT**. Data types and structures are precisely aligned across all schemas.

---

## 4. Audit Reconciliation Notes (Cross-Reference)

The contracts above constitute the **frozen canonical Stage 1 payload specification** and are internally consistent and deterministic. As documented in the companion `contract_consistency_matrix.md` and `validation_report.md`, the repository also co-residents additional contract generations (Phase 3 `simulator/`+`ingestion/`+`database/`+`integration/`) that use alternative envelope shapes (rich `machine_id`/`sensor_id` strings, scalar `value`/`quality`) and alternative storage tables. Those divergences are out of scope for *this* schema-audit verdict but are tracked as **JSON-01 / DB-02 / DB-03 / DB-04** in the master register and must be reconciled before the Stage 4 Contract Freeze.

**Action for freeze:** Adopt the four schemas in §2 as the single, semver-stamped source of truth; every producer and validator (canonical and Phase 3) must cite this schema version. This closes **Risk 1 (Undocumented Schema Divergence)** for the canonical path.
