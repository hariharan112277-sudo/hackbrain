# Alarm API

Alarm lifecycle endpoints consume the `IAlarmRepository` contract.

## GET /api/v1/industrial/alarms

List active (non-cleared) alarms.

**Query parameters:**
- `severity` (optional): `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

## POST /api/v1/industrial/alarms/{alarm_id}/resolve

Acknowledge / clear an alarm.

**Request body:**

```json
{
  "resolved_by": "operator-badge-123"
}
```

**Response:**

```json
{
  "success": true,
  "data": true,
  "message": "Alarm <id> resolved by operator-badge-123"
}
```

## Severity Levels

- `INFO`
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

## Access Control

Alarm resolution requires the `admin` or `operator` role.
