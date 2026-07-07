# MQTT Topic Topology & Contract Validation Report

**Stage:** 2 — Contract Validation, Alignment & Audit
**Owner:** Member 2 (Industrial Operating Brain — Data Foundation)
**Document ID:** `MQTT-CONTRACT-VAL-v1.0`
**Standards Alignment:** ISA-95 hierarchical levels (Enterprise / Site / Area / Cell / Device), ISO/IEC 20922 (MQTT)
**Audit Date:** 2026-07-07 (UTC)
**Contract Baseline:** Canonical Stage 1 generation (`iob_data_engine` / `src/` + `config/simulator_config.yaml`)

---

## 1. Purpose & Scope

This document audits the Unified Namespace (UNS) MQTT topic hierarchy designed for the Industrial Operating Brain (IOB). It ensures strict structural compatibility with ISA-95 hierarchical levels and verifies message quality criteria for high-frequency industrial ingestion.

---

## 2. Topic Hierarchy & Naming Conventions

The standard topic hierarchy is structured as follows:

```
iob/uns/<site_id>/<area_id>/<device_id>/<data_type>
```

### Evaluated Topic Matrix

1. **Telemetry:** `iob/uns/site_alpha/area_machining/cnc001/telemetry`
2. **Alarms:** `iob/uns/site_alpha/area_machining/cnc001/alarm`
3. **Machine State:** `iob/uns/site_alpha/area_machining/cnc001/state`
4. **Heartbeat:** `iob/uns/site_alpha/area_machining/cnc001/heartbeat`

---

## 3. Compliance Audit

### Quality of Service (QoS) & Retained Settings

* **Telemetry Data:** Configured for **QoS 1** (At least once delivery) to prevent data gaps during industrial network degradation. Retain flag set to **False** to prevent stale time-series ingestion loops upon subscriber re-connection.
* **State & Alarm Data:** Configured for **QoS 1** with Retain flag set to **True**. This provides immediate initialization context for the Frontend (Member 4) and Backend (Member 1) networks when spinning up fresh consumption clients.
* **Heartbeat Data:** Configured for **QoS 0** (At most once), Retain flag **False**. Transmission occurs at 0.5 Hz; dropped frames are acceptable due to low transient impact.

**Audit verification:** The canonical publisher (`src/simulator/core_simulator.py`) issues telemetry at `qos=1`; the canonical subscriber (`src/ingestion/mqtt_client.py`) binds `iob/uns/#` at `qos=1`. The end-to-end effective telemetry QoS is **1**, satisfying the at-least-once delivery requirement.

### Topic Ownership Boundaries

* **Publisher:** Strictly owned by Member 2's IndustrialSimulator. No other module is authorized to publish directly onto the `iob/uns/#` namespace.
* **Subscriber:** Handled exclusively by the TelemetryIngestionWorker.

---

## 4. Assessment & Scalability

* **Naming Consistency:** Complies with lowercase alphanumeric standards separated by underscores. No special characters or spaces exist within topic definitions.
* **Future Scalability:** Highly extensible. Adding a new facility or machine profile requires zero modification to the subscriber engine wildcard handling (`iob/uns/#`).
* **Verdict:** **COMPLIANT**. Topic topology is structurally sound and ready for contract freeze.
