# API Inventory Matrix (api_inventory.md)

This section maps all contracts exposed across the enterprise domain boundary.

| Domain Subsystem | Method | URI Path | Primary Consumers | Upstream Dependencies | Target Implementation Phase |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Auth** | POST | /api/v1/auth/token | Member 4 (UI), Member 3 (AI) | Cache, Identity Provider | Phase 3 (Sprint 1) |
| **Auth** | POST | /api/v1/auth/revoke | Member 4 (UI) | Token Cache | Phase 3 (Sprint 1) |
| **Machine Metadata** | GET | /api/v1/machines | Member 4 (UI), Member 3 (AI) | MachineRepository | Phase 3 (Sprint 2) |
| **Machine Metadata** | POST | /api/v1/machines | Member 4 (UI) | MachineRepository | Phase 3 (Sprint 2) |
| **Telemetry** | GET | /api/v1/telemetry/live | Member 4 (UI), Member 3 (AI) | TelemetryRepository, Broker | Phase 3 (Sprint 3) |
| **Historical Data** | POST | /api/v1/historical/query | Member 3 (AI), Member 4 (UI) | HistoricalRepository | Phase 3 (Sprint 4) |
| **Alarms** | GET | /api/v1/alarms/active | Member 4 (UI) | AlarmRepository | Phase 3 (Sprint 2) |
| **Alarms** | PATCH | /api/v1/alarms/{id}/acknowledge | Member 4 (UI) | AlarmRepository, Notification | Phase 3 (Sprint 2) |
| **Maintenance** | POST | /api/v1/maintenance/schedule | Member 4 (UI), Member 3 (AI) | MaintenanceRepository | Phase 3 (Sprint 5) |
| **Dashboard** | GET | /api/v1/dashboard/summary | Member 4 (UI) | Core Aggregate Service Layer | Phase 3 (Sprint 6) |
| **Health** | GET | /healthz | DevOps, Orchestrator Infrastructure | Core Infrastructure Tiers | Phase 3 (Sprint 1) |

## Contract Module Mapping

| URI Path | Programmatic Contract Location |
|---|---|
| `/api/v1/auth/token` | `integration.backend_contracts.TokenObtainRequest`, `TokenResponse` |
| `/api/v1/auth/revoke` | `integration.backend_contracts.TokenRevokeRequest` |
| `/api/v1/machines` | `MachineResponse`, `MachineSummaryResponse`, `PaginationParams` |
| `/api/v1/telemetry/live` | `TelemetryStreamRequest`, `TelemetryPointResponse` |
| `/api/v1/historical/query` | `HistoricalQueryRequest`, `HistoricalQueryResponse` |
| `/api/v1/alarms/active` | `AlarmFilterRequest`, `AlarmResponse` |
| `/healthz` | `HealthCheckResponse`, `SubsystemStatus` |
