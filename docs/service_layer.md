# Service Layer Design

The Phase 4 service layer sits between the REST controllers (`app/api`) and the repository abstraction (`app/repositories`). It is responsible for business rules, orchestration, and schema mapping.

## Services

| Service | Responsibility |
|--------|----------------|
| `AuthService` | Password verification, JWT issuance/refresh, token introspection |
| `UserService` | User lifecycle (CRUD) with in-memory store (replaceable) |
| `IndustrialService` | Orchestrates machine, telemetry, alarm, and metadata operations |
| `DashboardService` | Aggregates fleet-wide KPIs and chart series |

## Decoupling Rules

1. **Controllers do not access repositories directly.** They always depend on services.
2. **Services depend on repository interfaces, not implementations.** This preserves the Member 1 / Member 2 boundary.
3. **Domain exceptions flow through the global exception handler** registered in `app.core.exceptions`.

## Repository Modes

The `PHASE4_REPOSITORY_MODE` setting controls wiring:

- `stub` (default): In-memory repositories seeded with demo data. Ideal for tests and demos.
- `integration`: Adapters that delegate to the existing Member 2 integration services and SQLAlchemy repositories.

Switch modes via environment variable:

```bash
export PHASE4_REPOSITORY_MODE=integration
```

## Adding a New Endpoint

1. Define request/response schemas in `app/schemas/`.
2. Add business logic in the appropriate service in `app/services/`.
3. Expose the endpoint in the relevant router under `app/api/`.
4. Add a test under `tests/`.
