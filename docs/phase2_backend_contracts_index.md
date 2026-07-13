# Phase 2 Backend Contracts Index

This file wires the Phase 2 backend contract package into the existing `docs/` directory without changing runtime behavior.

## Primary Package

See the project-root package:

```text
Phase2_Backend_Contracts/
├── README.md
└── docs/
    ├── architecture/
    ├── contracts/
    ├── diagrams/
    ├── dto/
    ├── integration/
    ├── models/
    ├── openapi/
    ├── reports/
    └── templates/
```

## Programmatic Contract Module

The frozen external/backend Pydantic schemas are available at:

```python
from integration.backend_contracts import (
    TokenObtainRequest,
    TokenResponse,
    HistoricalQueryRequest,
    HistoricalQueryResponse,
    TelemetryQueryRequest,
    TelemetryStreamRequest,
    AssetTreeRequest,
    AlarmQueryRequest,
    AlarmAcknowledgeRequest,
    AggregationRequest,
    TelemetryPointResponse,
    HealthCheckResponse,
    ProblemDetails,
    ProblemDetailsResponse,
    ApiEnvelope,
    PaginatedResponse,
)
```

## Runtime Safety

No FastAPI routers, storage sessions, repository implementations, MQTT client loops, or AI workloads are introduced by Phase 2. The package is additive and contract-only.
