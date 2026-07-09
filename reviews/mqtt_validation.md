# MQTT Enterprise Infrastructure Validation Protocol

**IOB Stage 4 — Industrial IoT & Data Engineering Verification**

### 1. Protocol Configuration Audit

The network transport profiles have been reviewed against enterprise reliability requirements.

*   **Topic Naming Quality:** Verified compliance with the flat Unified Namespace (UNS) structure. No wildcards are hardcoded within ingestion services.
*   **Quality of Service (QoS) Enforcement:**
    *   Continuous Telemetry Streams: Configured to **QoS 1** (At least once) to maximize pipeline delivery.
    *   Critical Fault & Alarm Events: Configured to **QoS 2** (Exactly once) to prevent lost or duplicate alerts.
*   **Retained Message Configuration:** Enabled exclusively for the machine_metadata and version topic paths. This ensures that new client connections instantly receive the current machine state configuration without having to wait for the next data cycle.

UNS Topic Pattern Verified:
```
site/area/line/cell/device/telemetry
IOB_GLOBAL/CAPS_01/PAD_02/MAL_05/MC_CNC_01_A/telemetry
IOB_GLOBAL/CAPS_01/PAD_02/MAL_05/MC_CNC_01_A/alarms  (QoS 2)
IOB_GLOBAL/CAPS_01/PAD_02/MAL_05/MC_CNC_01_A/status  (retained, LWT)
```

### 2. Status Heartbeat Design

The status system monitors system health using a Last Will and Testament (LWT) message pattern. If a device disconnects unexpectedly, the MQTT broker automatically publishes a STATUS_OFFLINE flag to the device's health topic tree.

LWT Configuration:
- will_topic: `IOB_GLOBAL/CAPS_01/PAD_02/MAL_05/MC_CNC_01_A/status`
- will_payload: `{"status":"OFFLINE","asset_id":"MC_CNC_01_A","ts":<iso>}`
- will_qos: 2
- will_retain: true

Heartbeat: 30s interval, QoS 1

**Status: MQTT ENTERPRISE INFRASTRUCTURE — VERIFIED COMPLIANT**
