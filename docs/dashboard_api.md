# Dashboard API

The dashboard endpoint aggregates fleet-wide operational intelligence into a single payload optimized for frontend rendering.

## GET /api/v1/dashboard/summary

Returns:

```json
{
  "success": true,
  "data": {
    "generated_at": "2026-07-14T05:45:00Z",
    "total_machines": 12,
    "online_machines": 11,
    "offline_machines": 1,
    "active_alarms": 3,
    "critical_alarms": 0,
    "kpis": [
      { "title": "Fleet Availability", "value": 91.67, "unit": "%" },
      { "title": "Active Alarms", "value": 3, "unit": "count" }
    ],
    "health_tiles": [
      {
        "machine_id": "...",
        "name": "Demo CNC Lathe",
        "status": "ONLINE",
        "health_score": 98.5,
        "active_alarms": 1,
        "last_seen": "2026-07-14T05:44:59Z"
      }
    ],
    "charts": [
      {
        "name": "Demo CNC Lathe",
        "metric": "vibration",
        "unit": "mm/s",
        "timestamps": ["..."],
        "values": [2.1, 2.3, 2.2]
      }
    ]
  }
}
```

## Notes

- Health tiles are limited to the first 10 machines to control payload size.
- Chart series are built from the `vibration` metric by default.
- All timestamps are UTC ISO 8601.
