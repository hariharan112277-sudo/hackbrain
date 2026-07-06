# 7. Alarm JSON Schema

Alarms define state-based operational deviations requiring automated tracking or human operator acknowledgement.

## 7.1 Field Definitions & Structural Requirements

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "IOB_Alarm_Payload",
  "type": "object",
  "properties": {
    "alarm_id": { "type": "string", "format": "uuid" },
    "timestamp": { "type": "string", "format": "date-time" },
    "severity": { "type": "string", "enum": ["CRITICAL", "WARNING", "INFORMATION", "MAINTENANCE"] },
    "priority": { "type": "integer", "minimum": 1, "maximum": 100 },
    "machine_id": { "type": "string" },
    "sensor_id": { "type": "string" },
    "description": { "type": "string" },
    "current_value": { "type": ["number", "string", "boolean"] },
    "threshold_value": { "type": ["number", "string", "boolean"] },
    "acknowledgement": {
      "type": "object",
      "properties": {
        "is_acknowledged": { "type": "boolean" },
        "acknowledged_by": { "type": ["string", "null"] },
        "ack_timestamp": { "type": ["string", "null"], "format": "date-time" }
      },
      "required": ["is_acknowledged", "acknowledged_by", "ack_timestamp"]
    },
    "clear_condition": {
      "type": "object",
      "properties": {
        "auto_clear": { "type": "boolean" },
        "clear_timestamp": { "type": ["string", "null"], "format": "date-time" }
      },
      "required": ["auto_clear", "clear_timestamp"]
    },
    "operator_notes": { "type": "string" },
    "status": { "type": "string", "enum": ["ACTIVE", "ACKNOWLEDGED", "CLEARED", "SHELVED"] },
    "metadata": { "type": "object" }
  },
  "required": [
    "alarm_id", "timestamp", "severity", "priority", "machine_id", 
    "description", "current_value", "threshold_value", "acknowledgement", 
    "clear_condition", "status"
  ],
  "additionalProperties": false
}
```

## 7.2 Fully Populated Real-World Production Alarm Object

```json
{
  "alarm_id": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
  "timestamp": "2026-07-01T14:35:10.550Z",
  "severity": "CRITICAL",
  "priority": 95,
  "machine_id": "GMC_AUS_ASY_WLD01_ROB01",
  "sensor_id": "GMC_AUS_ASY_WLD01_ROB01_WRI05_TE01",
  "description": "Hydraulic Pressure Overpressure Safety Interlock Tripped",
  "current_value": 325.4,
  "threshold_value": 300.0,
  "acknowledgement": {
    "is_acknowledged": true,
    "acknowledged_by": "OP_USER_9021",
    "ack_timestamp": "2026-07-01T14:36:00.112Z"
  },
  "clear_condition": {
    "auto_clear": false,
    "clear_timestamp": null
  },
  "operator_notes": "Awaiting fluid cooling and physical valve relief verification.",
  "status": "ACKNOWLEDGED",
  "metadata": {
    "interlock_id": "IL_04_HYD",
    "safety_integrity_level": "SIL3"
  }
}
```