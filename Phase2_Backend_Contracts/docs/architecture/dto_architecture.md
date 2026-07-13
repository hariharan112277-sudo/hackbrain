# Data Transfer Object Architecture Map (dto_architecture.md)

## 1. Architecture Flow Mechanics

This diagram illustrates the lifecycle of a request as it transforms across layer boundaries.

```text
[ External Client Context ]
        │
        ▼  (HTTP JSON Payload / WS Text Stream Frame)
┌────────────────────────────────────────────────────────┐
│ 1. FastAPI / Pydantic Request Validation Model         │
└────────────────────────────────────────────────────────┘
        │
        ▼  (Implicit Mapping Validation Handshake via Service Factory)
┌────────────────────────────────────────────────────────┐
│ 2. Domain Application Ingestion DTO Layer              │
└────────────────────────────────────────────────────────┘
        │
        ▼  (Core Business Rule Executions & Context Enforcements)
┌────────────────────────────────────────────────────────┐
│ 3. System Infrastructure / Repository DTO Interface    │
└────────────────────────────────────────────────────────┘
        │
        ▼  (Member 2 Data Access Component Mapping Execution)
[ Database Entities / Storage Drivers / Persistent State Engine ]
```

## 2. Core Decoupling Transformation Design Rules

- **Decoupled Entities**: Under no circumstances should internal SQLAlchemy ORM classes, MongoDB raw documents, or Time-Series storage structural records be returned directly to the API boundary.
- **Transformation Isolation**: Transformations from RequestModel to internal ApplicationDTO must occur inside the API handler route definitions via constructor functions such as `DTO.model_validate(request)`.
- **Immutable Service Layer Boundaries**: The underlying business logic domain functions take internal DTO structures exclusively, isolating core features from dependencies on any choice of web frame layout.

## 3. Repository Wiring Rule

The Phase 2 package is additive to the existing repository. It introduces `integration/backend_contracts.py` for API-facing contracts while preserving `integration/contracts.py` for internal DTOs and `integration/interfaces.py` for service/repository abstractions.

## 4. Timestamp Drift DTO Rule

Telemetry response projections may expose:

- `edge_timestamp`: original timestamp emitted by the industrial edge node.
- `ingest_timestamp`: server UTC timestamp captured when the backend/ingestion boundary accepted the event.

The application mapping layer must never overwrite one timestamp with the other.
