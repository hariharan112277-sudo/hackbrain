# Production System Troubleshooting Guide (Task 12)

This reference manual provides clear diagnostic steps and solutions for common operational issues across the platform.

## Ingestion Pipeline Diagnostics Manual

### 1. Ingestion Interruption (MQTT Connection Drops)
* **Diagnostic Indicators:** The subscriber components output message alerts: `CRITICAL - [mqtt_service.py] Network transport link disconnected unexpectedly.`
* **Troubleshooting Action Steps:**
  1. Check network routing paths by pinging the EMQX cluster infrastructure container: `docker exec -it iob-subscriber ping iob-emqx-broker`.
  2. Verify that client authentication credentials and authorization parameters match the access rules configured in `config/mqtt_access_rules.yaml`.
  3. Restart the subscriber container instance to reset active network socket interfaces: `docker restart iob-subscriber-engine`.

### 2. Storage Bottlenecks (Database Query Timeouts)
* **Diagnostic Indicators:** Systems integration services log lookup failures: `IOBIntegrationException: Database query response timed out before commitment execution.`
* **Troubleshooting Action Steps:**
  1. Check the active connection pool allocation levels inside TimescaleDB: `SELECT count(*), state FROM pg_stat_activity GROUP BY state;`.
  2. Verify that historical lookback queries include both explicit tracking keys and indexed time boundaries (`timestamp`). Avoid executing open-ended full-table scans.
  3. Rebuild time-series index allocations across the target database partition blocks: `REINDEX TABLE telemetry;`.

### 3. Data Rejections (High Volumes of Dropped Packets)
* **Diagnostic Indicators:** Error logs output warnings: `WARNING - [validation.py] Packet serialization dropped due to schema validation failure.`
* **Troubleshooting Action Steps:**
  1. Inspect the isolated payloads in the dead-letter data tables to pinpoint validation failures.
  2. Compare the rejected message attributes against the field rules defined in the system schemas (`iob_telemetry_v1.json`).
  3. Verify that edge simulators or hardware gateways are using the correct engineering unit definitions and formatting timestamps as standardized ISO 8601 strings.
