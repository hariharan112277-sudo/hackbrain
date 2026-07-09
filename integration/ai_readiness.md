# Consumer Integration Readiness Brief: Member 3 (AI / GraphRAG)

**IOB Stage 4 — Member 2 Industrial IoT & Data Engineering → Member 3 Handover**

### 1. Provided Operational Deliverables

*   **Relational Asset Maps:** Comprehensive machine and sensor JSON configurations that outline physical equipment connections.
*   **Anomaly Training Sets:** Cleanly structured, synchronous data files that trace multi-regime anomalies back to confirmed mechanical errors.

Deliverables:
- `metadata/machine_metadata.json` — Machine registry
- `metadata/sensor_metadata.json` — Sensor registry
- `datasets/historical/telemetry_historical.csv` — 2.8M+ rows validated
- `datasets/alarms/alarm_dataset.json` — Anomaly labels
- `datasets/feature_dictionary.md` — ML feature map
- `datasets/config/features.yaml` — Feature pipeline

ISA-95 Graph anchors:
- Node: MC_CNC_01_A (Machine)
- Sensors: SN_VIB_XYZ_01, SN_TMP_CORE_02, SN_PRES_02, SN_PWR_01
- Line: MAL_05
- Quality: 100.00% complete, 0 duplicates

### 2. Integration Prerequisites & Constraints

*   Graph building scripts should use the asset_id column as the master anchor node when mapping relations to telemetry datasets.

Additional:
- feature vectors: double-precision float8
- timestamps: strictly monotonic, UTC ISO 8601
- labels: OMAC PackML standard literals
- training set: 100% schema compliant, referential integrity verified
- null density: 100.00% complete (timestamp, asset_id, machine_state)

**Status: AI / GraphRAG READINESS — CERTIFIED**
