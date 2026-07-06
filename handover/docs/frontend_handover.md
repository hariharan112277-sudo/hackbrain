# Frontend Integration Handover Manual (Target: Member 4)

## 1. Unified Machine Status State Engine

```text
  ┌───────────────┐        Maintenance Window Triggered        ┌─────────────────┐
  │               │───────────────────────────────────────────>│                 │
  │    ONLINE     │                                            │   MAINTENANCE   │
  │   (Normal)    │<───────────────────────────────────────────│  (Orange Code)  │
  │               │         Equipment Returned to Service      └─────────────────┘
  └───────────────┘                                                     │
    ▲           │                                                       │
    │           │ Communications Loss Event                             │ Complete
    │           ▼                                                       │ Decommission
  ┌───────────────┐                                                     ▼
  │    OFFLINE    │                                            ┌─────────────────┐
  │  (Grey Code)  │───────────────────────────────────────────>│ DECOMMISSIONED  │
  │               │          Permanent Removal From Site       │   (Black Code)  │
  └───────────────┘                                            └─────────────────┘
```

## 2. Live Dashboard Update Cadences
* **High-Frequency Telemetry Dashboards:** Chart rendering frames must use an asynchronous polling window or continuous push loop throttled to a **1-second interval (`1000ms`)**.
* **Global Asset Health Matrices:** Update the overview grid every **30 seconds (`30000ms`)**.

## 3. Production JSON Integration Payloads (`/api/v1/industrial/machines/{machine_id}/status`)

```json
{  
  "machine_id": "8c4b18c0-51a2-4db0-96ef-2782bcfb2111",  
  "display_name": "Primary Milling Axis Centrifuge CNC-102",  
  "current_status": "ONLINE",  
  "aggregate_health_score": 94.6,  
  "active_critical_alarms_count": 0,  
  "last_updated_timestamp": "2026-07-03T13:53:11Z"  
}
```
