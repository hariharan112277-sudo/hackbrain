# Machine API

Machine registry endpoints consume the `IMachineRepository` contract.

## GET /api/v1/industrial/machines

List registered machines with pagination.

**Query parameters:**
- `skip` (int, default 0)
- `limit` (int, default 100, max 1000)

## GET /api/v1/industrial/machines/{machine_id}

Return full machine details.

```json
{
  "success": true,
  "data": {
    "id": "...",
    "name": "Demo CNC Lathe",
    "status": "ONLINE",
    "current_mode": "AUTOMATIC",
    "health_score": 98.5,
    "capabilities": ["AUTO_MODE", "VIBRATION_MONITORING"],
    "metadata": {}
  }
}
```

## Error Responses

- `404 Not Found`: Machine ID does not exist.
- `401 Unauthorized`: Missing or invalid token.
