# JSON Schema Validation Specification (Task 4)

## 1. Ingestion Telemetry Schema (`iob_telemetry_v1.json`)
* **Root Properties Type:** `Object` (`"additionalProperties": false`).

| Field Pointer Token | Required Property | Data Type | Validation Rules / Range Constraints | Purpose & Structural Intent |
| :--- | :--- | :--- | :--- | :--- |
| `timestamp` | **True** | String | ISO 8601 UTC Z format style execution match | Event timestamp captured directly at the edge sensor interface. |
| `machine_id` | **True** | String | Canonical RFC-4122 Compliant UUIDv4 layout | Unique identifier for the source equipment asset wrapper. |
| `sensor_id` | **True** | String | Canonical RFC-4122 Compliant UUIDv4 layout | Unique identifier matching a registered hardware tracking instance. |
| `measured_value` | **True** | Float | Float64 format precision parameters | The raw physical measurement read from the edge hardware. |
| `quality_code` | **True** | Integer | Strict set inclusion choice constraint: `[0, 64, 128, 192]` | Enforces industrial OPC-DA signal quality classification standards. |
| `sequence_number` | **False** | Integer | Minimum boundary constraint: `>= 0` | An incremental counter used to detect packet loss across data links. |

## 2. Active Alarm Tracking Schema (`iob_alarm_v1.json`)
* **Root Properties Type:** `Object` (`"additionalProperties": false`).

| Field Pointer Token | Required Property | Data Type | Validation Rules / Range Constraints | Purpose & Structural Intent |
| :--- | :--- | :--- | :--- | :--- |
| `id` | **True** | String | Canonical UUIDv4 validation match | Unique identifier tracking this specific alarm occurrence lifecycle. |
| `machine_id` | **True** | String | Canonical UUIDv4 validation match | The equipment asset identifier that generated the system alarm. |
| `severity` | **True** | String | Strict Enum limit mapping: `[INFO, LOW, MEDIUM, HIGH, CRITICAL]` | Defines the operational threat level and determines the support response routing. |
| `state` | **True** | String | Strict Enum limit mapping: `[ACTIVE, ACKNOWLEDGED, CLEARED]` | Tracks the structural status of the alarm lifecycle. |
| `trigger_timestamp` | **True** | String | ISO 8601 UTC format match validation | The timestamp when the process parameter crossed the alarm threshold. |
| `clear_timestamp` | **False** | String | Nullable / ISO 8601 validation format | The timestamp when the process parameter returned to safe operating limits. |
