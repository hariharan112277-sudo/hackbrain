# Frontend Compatibility & UI Rendering Interface

**Target Consumer:** Member 4 (Frontend UI UX Developer)

This document profiles payload sizing, data types, and update frequencies to help Member 4 build clean, stable dashboard components.

## 1. UI Payload Properties Matrix

| Payload Stream Target | Average JSON Size | Target Refresh Window | UI Component State Behavior |
| :--- | :--- | :--- | :--- |
| **Machine Status Object** | `~1.4 KB` | `1000ms` (1 Second Loop) | Drives real-time status indicators (e.g., Online, Offline, Maintenance). |
| **Active Alarm Records** | `~850 Bytes` | Event-Driven (Instant Push) | Triggers immediate structural alert overlays on the plant map. |
| **Historical Trends Vector** | `~24.0 KB` | On-Demand (User Load Action) | Populates historical time-series analytics charts. |

## 2. Ingestion Response Properties
* **Temporal Consistency:** Every JSON time key is delivered as a standardized ISO 8601 string (`YYYY-MM-DDTHH:mm:ss.sssZ`).
* **Payload Constraints:** Telemetry arrays are throttled to a maximum of 1,440 data points per query window to prevent browser performance issues during chart rendering.
