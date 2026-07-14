# Historical Telemetry API

Retrieve time-series data for visualization and AI/ML consumption.

## GET /api/v1/industrial/machines/{machine_id}/telemetry/history

**Query parameters:**
- `metric` (required): metric name, e.g. `vibration`, `temperature`, `pressure`
- `limit` (int, default 100, max 1000)

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "...",
      "machine_id": "...",
      "sensor_id": "...",
      "metric": "vibration",
      "value": 2.1,
      "timestamp": "2026-07-14T05:44:00Z",
      "quality_code": 192
    }
  ],
  "meta": {
    "machine_id": "...",
    "metric": "vibration",
    "count": 1
  }
}
```

## Integration Mode Behavior

When `PHASE4_REPOSITORY_MODE=integration`, the adapter queries the SQLAlchemy
`Telemetry` table filtered by sensor type matching the requested metric.

## Notes

- OPC quality code `192` indicates "Good Quality".
- Timestamps are returned as UTC ISO 8601 strings.
