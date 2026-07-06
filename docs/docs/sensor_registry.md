# 4. Sensor Registry Specification

Every instrumentation point must be explicitly declared within the central registry before any telemetry ingestion processor will validate its messages.

## 4.1 Sensor Parameter Definitional Matrix

| Parameter Name     | Data Type | Permitted Engineering Units (Standard)          | Standard Sampling Frequencies          | Validation Boundary Range      |
|--------------------|-----------|------------------------------------------------|----------------------------------------|--------------------------------|
| Temperature        | Float     | `CELSIUS`, `KELVIN`                            | 1 Hz, 5 Hz, 10 Hz                      | -50.0 to 1200.0                |
| Pressure           | Float     | `BAR`, `PSI`, `PASCAL`                         | 10 Hz, 50 Hz                           | 0.0 to 400.0                   |
| Flow Rate          | Float     | `LITERS_PER_MIN`, `CUBIC_METERS_PER_HOUR`      | 2 Hz, 10 Hz                            | 0.0 to 5000.0                  |
| Vibration          | Array     | `MM_PER_SEC` (RMS), `G_FORCE` (Acceleration)   | 1000 Hz, 5000 Hz                       | 0.0 to 50.0                    |
| Current            | Float     | `AMPERE`                                       | 50 Hz, 60 Hz                           | 0.0 to 2000.0                  |
| Voltage            | Float     | `VOLT`                                         | 50 Hz, 60 Hz                           | 0.0 to 690.0                   |
| Power              | Float     | `WATT`, `KILOWATT`                             | 1 Hz, 10 Hz                            | 0.0 to 500000.0                |
| Rotational Speed   | Float     | `RPM`                                          | 10 Hz, 100 Hz                          | 0.0 to 15000.0                 |
| Torque             | Float     | `NEWTON_METER`                                 | 10 Hz, 100 Hz                          | 0.0 to 10000.0                 |

## 4.2 Field Definitions & Rules

- **Sensor ID:** Unified deterministic FLUID string extending to the sensor node level. Max 100 characters.
- **Precision (Resolution):** Expressed as an integer defining valid decimal points (e.g., `4` denotes evaluation down to $0.0001$).
- **Threshold & Alarm Strategy:** Must implement a 4-tier deadband filtering layout:
  - `HighCritical` → Immediate safety trip / E-stop request event generated.
  - `HighWarning` → Warning event emitted; operational optimization trigger.
  - `LowWarning` → Warning event emitted; process starvation warning.
  - `LowCritical` → Critical event emitted; structural starvation or pump cavitation hazard.