# 8. Industrial Event Schema

Events track system state transitions and contextual changes, establishing chronological sequencing across the facility floor.

## 8.1 Unified Event Structure Model Matrix

| Event Type          | Context/Origin              | Core Schema Tail Fields                              | Cross-Reference Entity IDs          |
|---------------------|-----------------------------|------------------------------------------------------|-------------------------------------|
| `MACHINE_STARTED`   | PLC Executive Run           | `target_recipe_id`, `target_speed`                   | Machine ID, Shift ID                |
| `MACHINE_STOPPED`   | Cycle End / Line Stop       | `reason_code`, `total_parts_produced`                | Machine ID, Shift ID                |
| `EMERGENCY_STOP`    | E-Stop Safety Circuit       | `e_stop_button_id`, `safety_relay_state`             | Machine ID, Device ID               |
| `OPERATOR_LOGIN`    | HMI Interlock Terminal      | `badge_auth_method`, `clearance_level`               | Operator ID, Device ID              |
| `OPERATOR_LOGOUT`   | HMI Timeout/Manual          | `duration_seconds`, `hmi_terminal_id`                | Operator ID, Device ID              |
| `MAINTENANCE_START` | Maximo / SAP PM             | `work_order_id`, `isolation_verified`                | Machine ID, Operator ID             |
| `MAINTENANCE_COMP`  | Maximo / SAP PM             | `parts_replaced_list`, `test_run_result`             | Machine ID, Operator ID             |
| `SHIFT_CHANGE`      | Plant ERP Scheduler         | `incoming_shift_id`, `outgoing_shift_id`             | Plant ID, Shift ID                  |
| `CONFIG_UPDATED`    | Engineering Workstation     | `parameter_name`, `old_val`, `new_val`               | Machine ID, Device ID               |
| `ALARM_TRIGGERED`   | Internal Interlock          | `alarm_id`, `initial_severity`                       | Machine ID, Sensor ID               |
| `ALARM_CLEARED`     | Internal Interlock          | `alarm_id`, `duration_milliseconds`                  | Machine ID, Sensor ID               |
| `SENSOR_FAILURE`    | I/O Driver Baseline         | `fault_type`, `diagnostic_register`                  | Machine ID, Sensor ID               |
| `COMM_FAILURE`      | Network Broker Driver       | `packet_loss_pct`, `retry_attempts`                  | Device ID, Gateway ID               |

## 8.2 Event Structural Schema Implementation Mapping Instance

```json
{
  "event_id": "01HAR9J5EZ4K7X1S9K741B2100",
  "event_type": "EMERGENCY_STOP",
  "timestamp": "2026-07-01T14:38:22.912345Z",
  "source_component": "PLC_MAIN_WLD01",
  "payload_attributes": {
    "e_stop_button_id": "ES_LINE_1_STATION_4",
    "safety_relay_state": "DE_ENERGIZED",
    "braking_sequence_initiated": true,
    "line_pressure_bar": 12.1
  },
  "related_entities": [
    { "entity_type": "MACHINE", "entity_id": "GMC_AUS_ASY_WLD01_ROB01" },
    { "entity_type": "SHIFT", "entity_id": "SHT_AUSTIN_2026_07_01_AM" },
    { "entity_type": "OPERATOR", "entity_id": "OP_USER_9021" }
  ]
}
```