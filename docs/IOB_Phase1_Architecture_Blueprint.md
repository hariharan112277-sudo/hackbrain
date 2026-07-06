# Industrial Operating Brain (IOB): Phase 1 Architecture Blueprint

**Document Version:** 1.0.0-RELEASE

**Classification:** Enterprise Internal Architecture Specification

**Standard Compliance:** ISA-95 (Enterprise-Control System Integration), ISA-88 (Batch Control), IEC 62541 (OPC-UA), ISO/IEC 20922 (MQTT 3.1.1/5.0)

## 1. Project Overview & Architecture Philosophy

The Industrial Operating Brain (IOB) relies on a deterministic, decoupled, and immutable **Industrial Data Foundation**. This blueprint establishes the strict data contracts, schemas, unified namespaces, and relational models required to ingest, contextualize, and distribute industrial telemetry and transactional events at an enterprise scale.

By decoupling the operational data layer from consumer applications using a Unified Namespace (UNS) architecture and strict JSON schemas, the backend, frontend, and AI teams can build their respective modules against guaranteed structures, field validations, and relationships without fear of structural drift.

## 2. Complete Asset Hierarchy Specification (`docs/asset_hierarchy.md`)

This specification utilizes an adapted **ISA-95 Part 1 Equipment Hierarchy Model**, extending it down to the sub-component and sensor layer to bridge Operational Technology (OT) and Information Technology (IT).

See: [docs/asset_hierarchy.md](docs/asset_hierarchy.md)

## 3. Machine Registry Specification (`docs/machine_registry.md`)

See: [docs/machine_registry.md](docs/machine_registry.md)

## 4. Sensor Registry Specification (`docs/sensor_registry.md`)

See: [docs/sensor_registry.md](docs/sensor_registry.md)

## 5. MQTT Topic Hierarchy & Unified Namespace (UNS) Architecture (`docs/mqtt_topics.md`)

See: [docs/mqtt_topics.md](docs/mqtt_topics.md)

## 6. Telemetry JSON Schema (`docs/telemetry_schema.md`)

See: [docs/telemetry_schema.md](docs/telemetry_schema.md)

## 7. Alarm JSON Schema (`docs/alarm_schema.md`)

See: [docs/alarm_schema.md](docs/alarm_schema.md)

## 8. Industrial Event Schema (`docs/event_schema.md`)

See: [docs/event_schema.md](docs/event_schema.md)

## 9. Machine Metadata Schema (`docs/metadata_schema.md`)

See: [docs/metadata_schema.md](docs/metadata_schema.md)

## 10. PostgreSQL Relational & Structural Design Specification (`database/schema_reference.md`)

See: [database/schema_reference.md](database/schema_reference.md)

## 11. Assumptions and Future Integration Roadmap (`README.md`)

See: [README.md](README.md)