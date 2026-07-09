# Consumer Integration Readiness Brief: Member 4 (Frontend UI Dashboard)

**IOB Stage 4 — Member 2 Industrial IoT & Data Engineering → Member 4 Handover**

### 1. Provided Operational Deliverables

*   **Stream Payload Mockups:** Example JSON files that accurately mirror the real-time telemetry structures arriving on the MQTT network.
*   **Unified State Definitions:** Comprehensive lookup charts mapping state metrics directly to OMAC PackML standard literals.

Deliverables:
- `handover/examples/telemetry.json` — Live stream mockup
- `handover/examples/alarm.json` — Alarm payload
- `handover/examples/heartbeat.json` — Status LWT
- `handover/examples/machine.json` — Machine metadata
- `handover/examples/sensor.json` — Sensor metadata
- MQTT topics: UNS compliant `site/area/line/cell/device/telemetry`

Stream sample:
```json
{
  "timestamp": "2026-07-09T08:00:00Z",
  "asset_id": "MC_CNC_01_A",
  "machine_id": "MC_CNC_01_A",
  "sensor_id": "SN_VIB_XYZ_01",
  "measurement": "vibration",
  "value": 2.34,
  "unit": "mm/s",
  "quality": "GOOD",
  "site_id": "IOB_GLOBAL",
  "plant_id": "CAPS_01",
  "line_id": "MAL_05"
}
```

### 2. Integration Prerequisites & Constraints

*   The dashboard interface should use time-bucket aggregations when rendering historical graphs over 30 days to optimize browser rendering performance.

Additional UI guidance:
- Real-time stream: MQTT QoS 1, 30s heartbeat
- Historical queries: use `idx_telemetry_machine_timestamp`
- Data type: float8 double-precision
- Aggregation: daily pre-aggregation reduces payload 85%
- State literals: OMAC PackML standard
- Refresh: 1 Hz max for 500 assets × 10 sensors

**Status: FRONTEND READINESS — CERTIFIED**
