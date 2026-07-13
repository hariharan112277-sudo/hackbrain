# Project Contract Review

## 1. Purpose & Core Scope
This document evaluates the boundary between the Industrial IoT domain (Member 2) and the Enterprise API/backend layer. The objective is schema compatibility for high-frequency telemetry, structural asset metadata, alarm/event vectors, historical query patterns, and AI/frontend consumption.

## 2. Ingestion & Storage Architecture Review
Member 2 exposes access through abstract interfaces and integration services rather than direct storage drivers. The existing repository contains:

- `database/interfaces.py` for generic persistence abstractions.
- `integration/interfaces.py` for service-level contracts consumed by application/API layers.
- `integration/contracts.py` for internal immutable DTOs.
- `integration/backend_contracts.py` for Phase 2 external request/response schemas.

## 3. Upstream Industrial Telemetry Contract
Validated inbound telemetry is represented as:

```python
class UpstreamTelemetryMetric(ContractBaseModel):
    name: str
    value: int | float | bool | str
    unit: str | None
    quality: TelemetryQuality
    metadata: dict[str, Any]

class UpstreamTelemetryPayload(ContractBaseModel):
    timestamp: datetime
    edge_node_id: str
    metrics: list[UpstreamTelemetryMetric]
```

**Verification Verdict:** Valid. The timestamp maps to time-series indexing and the metric list preserves Sparkplug-style multi-metric payloads while enforcing a bounded list size.

## 4. Metadata & Asset Hierarchies
The digital twin hierarchy uses machines as operational roots and sensors/components as leaves:

```python
class UpstreamAssetNode(ContractBaseModel):
    uuid: UUID
    parent_uuid: UUID | None
    node_type: NodeType  # GATEWAY | MACHINE | COMPONENT | SENSOR
    display_name: str
    attributes: dict[str, Any]
```

**Architectural Alignment:** `node_type` is aligned with the existing domain taxonomy and can map to `AssetDTO`, `MachineDTO`, and `SensorDTO` without changing repository behavior.

## 5. Boundary Integration Risk Matrix

| Risk | Contractual Mitigation | Verification Rule |
|---|---|---|
| Timestamp Drift | Preserve both `edge_timestamp` and `ingest_timestamp` in telemetry response payloads. | `TelemetryPointResponse` and `MetricDataPoint` expose both fields. |
| Schema Drift in Dynamic Attributes | Dynamic dictionaries remain typed as `dict[str, Any]` at the boundary, with JSON Schema validation required during Service-layer DTO mapping. | API layer must not persist or forward arbitrary metadata before structural validation. |

## 6. Frozen Boundary Statement
The following remain explicitly out of scope for Phase 2:

- FastAPI router registration.
- SQLAlchemy/session usage.
- MQTT subscribe/publish loops.
- AI inference, anomaly scoring, or operational decision logic.
- Authentication enforcement implementation.

Phase 2 freezes the shape, naming, validation, and lifecycle of external/backend contracts only.
