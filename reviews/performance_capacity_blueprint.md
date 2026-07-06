# Performance Optimization & Capacity Planning Blueprint

**Platform:** Industrial Operating Brain (IOB)  
**Document Owner:** Principal Industrial IoT Platform Owner

---

## 1. System Bottleneck Audit & Resource Envelopes

Based on stress testing results (`validation/metrics/throughput_results.csv`), our single-node ingestion engine operates within strict performance envelopes:
* **0 — 500 msg/sec:** Processing latency $\le 26.4\text{ms}$; CPU load $\le 37.1\%$; RAM allocation $\le 5.0\text{ GB}$. Highly stable.
* **1,000 msg/sec:** Processing latency reaches $26\text{ms}$ average / $45\text{ms}$ P95; CPU load reaches $38\%$. Database connection pools require scaling to `DB_POOL_SIZE=50` to avoid connection queue waits.
* **10,000 msg/sec:** CPU saturation ($98\%$) and memory spike ($14.2\text{ GB}$). Single Python subscriber thread becomes bottleneck.

---

## 2. Targeted Optimization Action Plan

### 2.1 Database Query & Storage Optimization
* **Hypertable Chunk Sizing:** Ensure `chunk_time_interval` is tuned to exact 7-day windows (`SELECT set_chunk_time_interval('telemetry', INTERVAL '7 days');`). Keeps active B-tree indices entirely in RAM.
* **Covering Indices:** Add covering index for high-frequency RUL lookups:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_telemetry_machine_metric_val ON telemetry(machine_id, timestamp DESC) INCLUDE (measured_value, quality_code);
  ```

### 2.2 MQTT Ingestion & Pipeline Concurrency
* **Batch Ingestion Buffer:** Adjust `MqttTelemetrySubscriber` queue handoff to accumulate 50 packets per batch before submitting to `TelemetryRepository.bulk_insert_telemetry()`. Reduces network RTT overhead by 80%.
