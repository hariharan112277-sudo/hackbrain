# 6. Telemetry JSON Schema

The unified telemetry structure provides a standardized envelope for every raw metric entering the IOB environment.

## 6.1 Telemetry JSON Schema Definition

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "IOB_Telemetry_Payload",
  "type": "object",
  "properties": {
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp accurate to nanosecond precision."
    },
    "asset_id": {
      "type": "string",
      "pattern": "ULID or explicit canonical FLUID schema representation mapping"
    },
    "machine_id": { "type": "string" },
    "sensor_id": { "type": "string" },
    "topic": { "type": "string" },
    "measurement": { "type": "string" },
    "value": {
      "type": ["number", "string", "boolean"],
      "description": "The raw calculated variant output parsed from instrument converter."
    },
    "unit": { "type": "string" },
    "quality": {
      "type": "string",
      "enum": ["GOOD", "BAD_UNCONFIGURED", "BAD_TIMEOUT", "UNCERTAIN_DEGRADED", "LIMIT_CLAMPED"]
    },
    "sequence_number": { "type": "integer", "minimum": 0 },
    "gateway_id": { "type": "string" },
    "site_id": { "type": "string" },
    "plant_id": { "type": "string" },
    "line_id": { "type": "string" },
    "processing_status": {
      "type": "string",
      "enum": ["RAW", "ENRICHED", "VALIDATED", "HISTORIZED"]
    },
    "metadata": { "type": "object" }
  },
  "required": [
    "timestamp", "asset_id", "machine_id", "sensor_id", "topic", 
    "measurement", "value", "unit", "quality", "sequence_number", 
    "gateway_id", "site_id", "plant_id", "line_id"
  ],
  "additionalProperties": false
}
```

## 6.2 Target Payload Production Verification Code Examples

### Standard Production Ingestion Example (Happy Path)

```json
{
  "timestamp": "2026-07-01T14:30:00.123456789Z",
  "asset_id": "GMC_AUS_ASY_WLD01_ROB01_WRI05_TE01",
  "machine_id": "GMC_AUS_ASY_WLD01_ROB01",
  "sensor_id": "GMC_AUS_ASY_WLD01_ROB01_WRI05_TE01",
  "topic": "gmc/aus/asy/wld01/rob01/telemetry/temperature",
  "measurement": "joint_5_motor_temperature",
  "value": 72.84,
  "unit": "CELSIUS",
  "quality": "GOOD",
  "sequence_number": 1045923,
  "gateway_id": "AUS_ASY_GW01",
  "site_id": "AUS",
  "plant_id": "ASY",
  "line_id": "WLD01",
  "processing_status": "RAW",
  "metadata": {
    "calibration_drift_factor": 0.002,
    "opc_ua_node_id": "ns=2;s=RoboticArm1.Wrist.MotorTemp"
  }
}
```

### Sensor Interface Hardware Malfunction Example (Error Path)

```json
{
  "timestamp": "2026-07-01T14:31:02.000000000Z",
  "asset_id": "GMC_AUS_ASY_WLD01_ROB01_WRI05_TE01",
  "machine_id": "GMC_AUS_ASY_WLD01_ROB01",
  "sensor_id": "GMC_AUS_ASY_WLD01_ROB01_WRI05_TE01",
  "topic": "gmc/aus/asy/wld01/rob01/telemetry/temperature",
  "measurement": "joint_5_motor_temperature",
  "value": -999.0,
  "unit": "CELSIUS",
  "quality": "BAD_TIMEOUT",
  "sequence_number": 1046104,
  "gateway_id": "AUS_ASY_GW01",
  "site_id": "AUS",
  "plant_id": "ASY",
  "line_id": "WLD01",
  "processing_status": "RAW",
  "metadata": {
    "error_code": "0x800A0004",
    "diagnostic_message": "PT100 RTD Open Circuit Detected - Loop Broken"
  }
}
```