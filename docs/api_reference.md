# API Reference

All Phase 4 endpoints are mounted under `/api/v1`.

## Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Obtain JWT access/refresh tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Current user profile |
| POST | `/api/v1/auth/introspect` | Decode and inspect a token |

## User Management

| Method | Path | Description | Access |
|--------|------|-------------|--------|
| GET | `/api/v1/users/me` | Current user profile | Any authenticated |
| GET | `/api/v1/users` | List users | admin |
| GET | `/api/v1/users/{id}` | Get user | admin |
| POST | `/api/v1/users` | Create user | admin |
| PATCH | `/api/v1/users/{id}` | Update user | admin |
| DELETE | `/api/v1/users/{id}` | Delete user | admin |

## Industrial

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/industrial/machines` | List machines |
| GET | `/api/v1/industrial/machines/{id}` | Get machine detail |
| GET | `/api/v1/industrial/machines/{id}/telemetry/latest` | Latest telemetry snapshot |
| GET | `/api/v1/industrial/machines/{id}/telemetry/history` | Historical telemetry |
| GET | `/api/v1/industrial/alarms` | Active alarms |
| POST | `/api/v1/industrial/alarms/{id}/resolve` | Resolve alarm |
| GET | `/api/v1/industrial/machines/{id}/metadata` | Machine metadata |

## Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/dashboard/summary` | Fleet-wide dashboard summary |

## Response Envelope

Every response follows the same envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "message": null,
  "meta": { ... }
}
```
