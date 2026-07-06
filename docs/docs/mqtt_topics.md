# 5. MQTT Topic Hierarchy & Unified Namespace (UNS) Architecture

The IOB leverages a structural, deterministic **Unified Namespace (UNS)** constructed over MQTT to serve as the unified real-time semantic data bus.

## 5.1 Topic Namespace Structure

The namespace structure guarantees that semantic placement directly matches physical operational placement, mapping the ISA-95 model cleanly:

`[Enterprise]/[Site]/[Plant]/[Line]/[Machine]/[MessageCategory]/[SubTopic]`

## 5.2 Complete Unified Namespace Structure Mapping Matrix

| Message Category     | Sub-Topic Element     | Allowed Payload Content Types          | QoS | Retain Flag | Expected Publishing Cadence                     |
|----------------------|-----------------------|----------------------------------------|-----|-------------|-------------------------------------------------|
| `telemetry`          | `[sensor_type]`       | Continuous physical stream JSON data   | 0   | `false`     | Time-sampled (1 Hz - 100 Hz)                    |
| `events`             | `[event_type]`        | State transitions, operational markers | 1   | `false`     | On-change spontaneous occurrences               |
| `commands`           | `[command_name]`      | Output target requests from orchestrator| 2   | `false`     | Spontaneous write request actions               |
| `configuration`      | `state`               | Machine control-parameter baseline updates | 1 | `true`      | On deployment or operator override              |
| `maintenance`        | `logs`                | Diagnostic trouble codes (DTC), run-hours | 1 | `true`      | Periodic execution or step completion           |
| `alerts`             | `[severity]`          | Active alarm states and process breaches | 2   | `true`      | Instantaneous on threshold violation            |
| `diagnostics`        | `network`             | Signal noise ratios, bandwidth, packet rates | 0 | `false`     | Periodic standard baseline (0.1 Hz)             |
| `health`             | `heartbeat`           | Dynamic watchdog standard payload      | 1   | `false`     | Cyclic interval (10 Seconds)                    |

## 5.3 Topic Construction Standards & Rules

- **Case Sensitivity:** Strict lower-case across all nodes within the MQTT topic path.
- **Allowed Separators:** Forward slash `/` as the structural hierarchy delimiter.
- **Prohibited Characters:** Spaces, wildcards (`+`, `#`), dollar signs (`$`), leading/trailing slashes, and special symbols (`?`, `!`, `@`, `*`).
- **Versioning Strategy:** Implemented within the sub-topic namespace for payload evolution mapping (e.g., `.../telemetry/v1/temperature`).

## 5.4 Subscription & Querying Patterns (Wildcard Matrix)

- **Monitor Whole Plant Ingestion:** `gmc/aus/asy/#`
- **Monitor Every Temperature Across Global Enterprise:** `+/+/+/+/+/telemetry/+/temperature`
- **Isolate All Machine Alarms in Site Line 1:** `gmc/aus/asy/wld01/+/alerts/#`

## 5.5 Topic Anti-Patterns (Forbidden Structuring)

- *Do not mix physical locations with logical groupings:* `gmc/telemetry/aus/asy/wld01` (Violates directional tree mapping).
- *Do not append timestamps to topics:* `gmc/aus/asy/wld01/rob01/telemetry/2026-07-01` (Causes linear connection path explosions on brokers).