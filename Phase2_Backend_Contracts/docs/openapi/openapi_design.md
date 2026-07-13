# Enterprise System OpenAPI Architecture Layout (openapi_design.md)

## 1. Core Structural Global Declarations

```yaml
openapi: 3.1.0
info:
  title: Industrial Operating Brain (IOB) Core Compute Engine API Engine
  version: 1.0.0
  description: High-reliability, low-latency API contracts facilitating Industry 5.0 monitoring capabilities.
servers:
  - url: https://iob.enterprise.internal/api/v1
    description: Internal Secure Operational Site Ingress Gateway
paths: {}
```

The executable OpenAPI companion file for repository integration is located at `integration/docs/openapi_phase2_contracts.yaml`.

## 2. Structural Endpoint Specification Matrix

### 2.1 Historical Time-Series Ingestion & Retrieval Node

- **HTTP Method Strategy**: `POST`
- **URI Mapping Location**: `/historical/query`
- **Tag Association**: `Industrial Telemetry Data Engine`
- **Security Baseline Enforcements**: `Bearer JWT Access Token Requirement` mapped to `Role Hierarchy: ['AI_ENGINE_CONSUMER', 'OPERATIONS_MANAGER']`.
- **Response Code Bindings**:
  - `200 OK`: Type payload bound to `HistoricalQueryResponse` schema layout structure.
  - `400 Bad Request`: Mapping constraint payload resolution exception mapped down to `ProblemDetailsResponse`.
  - `422 Unprocessable Entity`: Data shape validation structural errors array structure using `ERR_SYS_VAL_01`.

### 2.2 Live Telemetry Synchronization Stream Boundary

- **Protocol Mechanism**: `WebSocket (WS)`
- **URI Mapping Location**: `/telemetry/live`
- **Tag Association**: `Streaming Infrastructure Engine`
- **Security Baseline Enforcements**: Query token initialization validation parameters check.
- **Frame Contract**: Server emits `TelemetryPointResponse` frames and preserves `edge_timestamp` plus `ingest_timestamp` when available.

### 2.3 Authentication Token Boundary

- **HTTP Method Strategy**: `POST`
- **URI Mapping Location**: `/auth/token`
- **Request Contract**: `TokenObtainRequest`
- **Response Contract**: `TokenResponse`
- **Failure Mapping**:
  - `401 Unauthorized`: `ERR_SEC_ATH_01`
  - `422 Unprocessable Entity`: `ERR_SYS_VAL_01`

### 2.4 Health Diagnostics Boundary

- **HTTP Method Strategy**: `GET`
- **URI Mapping Location**: `/healthz`
- **Response Contract**: `HealthCheckResponse`
- **Security**: Infrastructure/orchestrator accessible; no business resource RBAC.

## 3. Enterprise Failure Mapping Binding

Every non-2xx response must emit RFC 7807 payloads using the matrix in `docs/models/error_model.md` and must include `correlation_id` except for pre-routing infrastructure outages where a correlation id cannot be established.
