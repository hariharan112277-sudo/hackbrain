# 3. Machine Registry Specification

The Machine Registry serves as the source of truth for every operational machine entity asset class inside the platform.

## 3.1 Field Dictionary and Validation Constraints

| Field Name            | Datatype | Validation Rules / Pattern                                                                 | Description                                                                 |
|-----------------------|----------|--------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `machine_id`          | String   | Regex: `^[A-Z0-9]{3}_[A-Z0-9]{3}_[A-Z0-9]{3}_[A-Z0-9_]{3,20}$`                            | Unified deterministic FLUID string up to machine level.                     |
| `machine_name`        | String   | Max 100 chars, alphanumeric with spaces/hyphens.                                           | Human-readable machine label.                                               |
| `machine_type`        | String   | Enum: `[ROBOTIC_ARM, CNC_MILL, INJECTION_MOLD, CONVEYOR, PUMP, COMPRESSOR, OVEN]`         | Functional classification of the machine.                                   |
| `manufacturer`        | String   | Max 100 chars.                                                                             | Original Equipment Manufacturer (OEM).                                      |
| `model`               | String   | Max 50 chars.                                                                              | Manufacturer-designated model number.                                       |
| `installation_date`   | Date     | ISO 8601 extended: `YYYY-MM-DD`. Must be ≤ current date.                                   | Calendar date when unit arrived physically on-site.                         |
| `commission_date`     | Date     | ISO 8601 extended. Must be ≥ `installation_date`.                                          | Calendar date when machine passed validation and was signed off.            |
| `location`            | String   | Format: `Lat:[-+]?[0-9]{1,2}\.[0-9]{4}, Long:[-+]?[0-9]{1,3}\.[0-9]{4}`                   | Physical location tags / exact coordinates within plant boundary.           |
| `production_line`     | String   | Must match valid Line level segment in FLUID.                                              | Structural assignment code.                                                 |
| `criticality`         | String   | Enum: `[CRITICAL, HIGH, MEDIUM, LOW]`                                                      | Impact tier on total plant throughput if asset fails.                       |
| `operating_status`    | String   | Enum: `[RUNNING, IDLE, BLOCKED, STARVED, FAULTED, OFFLINE]`                                | Current functional automation state.                                        |
| `maintenance_status`  | String   | Enum: `[OK, SCHEDULED, OVERDUE, UNDER_REPAIR, DECOMMISSIONED]`                             | Current lifecycle maintenance state.                                        |
| `asset_category`      | String   | Enum: `[PRODUCTION, UTILITY, LOGISTICS, QUALITY]`                                          | Broad enterprise domain classification.                                     |
| `serial_number`       | String   | Max 50 chars, alphanumeric. Unique per manufacturer.                                       | Physical serial plate identification string.                                |
| `firmware_version`    | String   | SemVer standard format: `^v?(0\|[1-9]\d*)\.(0\|[1-9]\d*)\.(0\|[1-9]\d*)$`                 | Current embedded control software layer tracking code.                      |
| `comm_protocol`       | String   | Enum: `[OPCUA, MQTT_SPARKPLUG, MODBUS_TCP, PROFINET, ETHERNET_IP]`                        | Primary ingestion layer network protocol.                                   |
| `gateway_assignment`  | String   | Must match a valid edge gateway network identifier.                                        | Edge concentrator node name managing data transport.                        |
| `associated_sensors`  | Array    | Array of valid Sensor FLUID strings.                                                       | Multi-element references linking instrumentation layer.                     |
| `supported_commands`  | Array    | Array of objects matching command structure definition.                                    | Explicit write-back capabilities validated by the control matrix.           |
| `metadata`            | JSONB    | Open schema format. Key-value depth limit: 3 levels.                                       | Dynamic attributes specific to unique machine variants.                     |