# Backend Integration Strategy Plan (backend_integration_plan.md)

This section defines the execution patterns for managing high-frequency telemetry and cross-layer state boundaries.

## 1. High-Frequency Telemetry Ingestion Flow Architecture

```text
[ MQTT Edge Broker Hub ] ──( Sparkplug B Frames )──> [ Consumer Engine Worker Processes ]
                                                              │
                                                              ▼
                                                [ Member 2 Storage Repository ]
                                                              │
                                                              ▼ (Database Commit Complete)
[ Client UI / AI Engines ] <──( WebSocket Nodes )── [ Backend Broadcast Layer Cache ]
```

## 2. Structural Boundary Integration Rules

### 2.1 Telemetry Data Pipelining

The backend layer remains completely isolated from direct MQTT processing loops. Member 2 consumes the message streams, structures the telemetry packets, and writes them to the database. The backend system interacts with this data exclusively through the `ITelemetryRepository` extraction methods or the application memory cache layer.

### 2.2 Shared Application State Cache Lifecycle

- **Technology Choice**: Redis In-Memory Structure Storage Tier.
- **Key Design Standard Strategy**: Active asset telemetry fields follow the strict layout format template `iob:telemetry:live:{machine_uuid}`.
- **Time-To-Live (TTL) Hard Constraint Enforcement**: All volatile caching keys maintain an automatic sliding expiration threshold window of exactly 60 seconds. This avoids the accumulation of stale sensor status information if an edge system unexpectedly disconnects.

## 3. Boundary Integration Risk Matrix

| Risk | Description | Mitigation Contract | Implementation Owner |
|---|---|---|---|
| Timestamp Drift | Edge telemetry clocks may drift relative to server UTC time. | Internal response models preserve both `edge_timestamp` and `ingest_timestamp`. | Backend API + Ingestion |
| Schema Drift in Dynamic Attributes | Upstream systems can insert arbitrary dictionary values. | Enforce structural JSON Schema validation inside the application Service layer DTO mapping phase. | Backend Service Layer |
| Storage Timeout | Time-series partitions may fail to respond within operational SLO. | Return `ProblemDetailsResponse` with HTTP `503` and `ERR_INF_DB_01`. | Repository Adapter + API Error Mapper |
| RBAC Drift | Role definitions may diverge between UI and backend. | Map endpoint authorization failures to HTTP `403` and `ERR_SEC_AUT_02`. | Security Middleware |

## 4. Non-Invasive Wiring

```python
from integration.backend_contracts import HistoricalQueryRequest, HistoricalQueryResponse
from integration.contracts import QueryCriteriaDTO, TelemetryDTO
```

No direct imports from `database.*` are needed at the API contract layer.

## 5. Mapping Example

```text
HistoricalQueryRequest
  -> QueryCriteriaDTO
  -> IHistoricalQueryService.get_historical_telemetry(...)
  -> list[TelemetryDTO]
  -> HistoricalQueryResponse / PaginatedResponse[TelemetryPointResponse]
```
