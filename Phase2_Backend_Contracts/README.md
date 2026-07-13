# Industrial Operating Brain (IOB) - Phase 2: Frozen Backend Contracts

## Purpose & Scope
This contract package establishes the structural, typing, and architectural boundaries for the IOB backend layer. It is the validation barrier between external HTTP/WebSocket clients, AI workloads (Member 3), frontend interfaces (Member 4), and the downstream hardware/storage components managed by the Industrial IoT layer (Member 2).

The package is contract-only. It does **not** introduce business logic, FastAPI routes, repository implementations, direct SQL/NoSQL access, or message broker consumers. All interfaces, schemas, validation frameworks, and data transfer paths are specified down to primitive and composite data types.

## Architectural Principles
- **Hexagonal / Clean Architecture boundaries**: API contracts are external representations; `integration.contracts` remains the internal DTO layer.
- **Idempotency and Traceability**: `X-Correlation-ID` is mandatory for every inbound request and propagated to every response/error envelope.
- **Zero-Trust Industrial Security Baseline**: RBAC decisions are represented contractually by endpoint role mapping and actor context; enforcement belongs to the future application layer.
- **Defensive Contract Validation**: Strict Pydantic v2 schemas block malformed telemetry, historical queries, alarm transitions, and asset hierarchy inputs before they reach compute/storage adapters.

## Repository Integration
This delivery is aligned to the existing `hackbrain` repository wiring:

- Existing DTOs are kept in `integration/contracts.py`.
- New external backend/API contract schemas are added in `integration/backend_contracts.py`.
- Documentation is packaged under `Phase2_Backend_Contracts/` so it can be copied directly to the project root.
- No existing runtime pipelines, MQTT subscribers, database repositories, or FastAPI routes are modified.

## Directory Manifest
- `docs/reports/api_inventory.md`: Domain-subsystem endpoint inventory and RBAC surface.
- `docs/dto/request_models.md` and `docs/dto/response_models.md`: Strict schema definitions including field constraints and examples.
- `docs/models/error_model.md`: Standardized RFC 7807 problem details structure.
- `docs/architecture/dto_architecture.md`: Data transformation phases and DTO boundary rules.
- `docs/models/database_mapping.md`: Relational/logical mapping from storage entities to external contracts.
- `docs/contracts/repository_contract_review.md`: Interface structural verification of Member 2 repository/service contracts.
- `docs/openapi/openapi_design.md`: REST and streaming boundary design.
- `docs/integration/backend_integration_plan.md`: Mechanics for telemetry, events, WebSocket streams, and contract promotion.
- `docs/templates/api_lifecycle.md`: Backwards compatibility, deprecation, and expansion policies.
