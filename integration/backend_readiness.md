# Consumer Integration Readiness Brief: Member 1 (Backend API)

**IOB Stage 4 — Member 2 Industrial IoT & Data Engineering → Member 1 Handover**

### 1. Provided Operational Deliverables

*   **Database Access Layer:** Optimized SQL script files containing the primary table architectures and index mappings.
*   **Seeding Data Sets:** Validated time-series CSV files that can be directly imported to populate historical data paths during development.

Deliverables included:
- `database/schema.sql` — Primary table architectures
- `database/seed.sql` — Initial seeding
- `database/repository.py` — PreparedBatchInterface (1000-row)
- `datasets/historical/telemetry_historical.csv` — Validated time-series
- `handover/schemas/iob_telemetry_v1.json` — Contract
- `integration/openapi_specs.yaml` — API surface

ISA-95 asset registry:
```
IOB_GLOBAL/CAPS_01/PAD_02/MAL_05/MC_CNC_01_A
```

### 2. Integration Prerequisites & Constraints

*   The Backend must read metric parameters as double-precision floats (float8).
*   Any manual insertions issued by the API layer must use the standardized UTC ISO 8601 format to prevent timestamp offset issues.

Additional constraints:
- MQTT QoS: Telemetry QoS 1, Alarms QoS 2
- Topic pattern: `site/area/line/cell/device/telemetry`
- Batch size: 1000-row micro-batch sliding window
- Validation: explicit type coercion at edge (float8)
- Timestamp: UTC ISO 8601 mandatory
- asset_id: master anchor key

**Status: BACKEND READINESS — CERTIFIED**
