# Enterprise Production Support & Monitoring Runbook

**Platform:** Industrial Operating Brain (IOB)  
**Version:** 1.0.0-PROD  
**Document Owner:** Principal Industrial IoT Platform Owner  
**Classification:** Internal Operations & Site Reliability Engineering (SRE)

---

## 1. Executive Summary & Production Support Charter

Following the successful release and sign-off of **IOB Version 1.0**, the platform operates as a mission-critical Level 2 / Level 3 industrial enterprise data backbone across global manufacturing sites. As Platform Owner, our objective is zero unplanned downtime, sub-30ms processing latency, and strict adherence to IEC 62443 security and ISA-95 data integrity standards.

This runbook establishes deterministic diagnostics, triage procedures, and Root Cause Analysis (RCA) protocols for continuous production support across seven core operational domains:
1. **MQTT Broker Fabric** (EMQX Enterprise Cluster)
2. **Persistence Storage Tier** (PostgreSQL / TimescaleDB Hypertables)
3. **Core Ingestion Pipeline** (MQTT Subscriber, Validation, Normalization, Parser)
4. **Telemetry Ingestion Streams** (QoS 1 high-frequency sensor matrices)
5. **Repository Abstraction Layer** (SQLAlchemy Session Scopes & DTO mappings)
6. **Historical Analytics Queries** (Paginated partition lookbacks)
7. **AI Dataset Preparation Engine** (Rolling feature accumulation & RUL labeling)

---

## 2. Continuous Monitoring & Diagnostic Runbooks

### 2.1 MQTT Publishing Failures & Dropped Messages
* **Symptoms:** Client disconnections logged in EMQX dashboard; edge publishers report socket write timeouts (`Errno 110 ETIMEDOUT`); `sequence_number` gaps observed in incoming telemetry stream.
* **Diagnostic Protocol:**
  1. Inspect EMQX cluster nodes for TCP connection exhaustion:
     ```bash
     docker exec -it iob-emqx-backbone emqx_ctl clients count
     docker exec -it iob-emqx-backbone emqx_ctl listeners
     ```
  2. Verify ACL authorization rejections in `/var/log/emqx/emqx.log` against `mqtt_access_rules.yaml`.
  3. Audit QoS 1 packet queues and inflight windows:
     ```bash
     docker exec -it iob-emqx-backbone emqx_ctl broker stats | grep inflight
     ```
* **Remediation:** If connection storms occur due to edge network flutter, verify exponential backoff algorithms on edge publishers. If EMQX inflight window is full, scale worker thread allocation in `iob-ingestion-subscriber`.

### 2.2 Database Latency & Connection Pool Contention
* **Symptoms:** Integration services throw `DatabaseUnavailableException` or `OperationalTimeoutError`; repository `bulk_insert_telemetry` exceeds 50ms execution envelope.
* **Diagnostic Protocol:**
  1. Audit PostgreSQL active connections and lock waits:
     ```sql
     SELECT pid, usename, state, wait_event_type, wait_event, query_start, query 
     FROM pg_stat_activity 
     WHERE state != 'idle' AND (now() - query_start) > interval '100 milliseconds';
     ```
  2. Check connection pool utilization metrics via `connection_manager`:
     ```bash
     docker exec -it iob-ingestion-subscriber python3 -c "from database.connection import connection_manager; print(connection_manager.engine.pool.status())"
     ```
* **Remediation:** If active sessions exceed 85% of `DB_POOL_SIZE` (25), dynamically scale connection limits via `pg_bouncer` multiplexing or adjust `DB_POOL_SIZE` parameter in environment profile during scheduled low-volume windows.

### 2.3 High CPU Saturation & Memory Leaks
* **Symptoms:** Host node CPU utilization sustained > 85%; container RAM footprint growing linearly towards cgroup OOM kill limits (`14.2 GB` threshold).
* **Diagnostic Protocol:**
  1. Audit container cgroup resource consumption:
     ```bash
     docker stats --no-stream iob-ingestion-subscriber iob-timescaledb-cluster
     ```
  2. Profile memory leaks in Python ingestion processes using `tracemalloc`:
     ```python
     import tracemalloc
     tracemalloc.start()
     # Inspect top memory allocations inside ingestion loop
     ```
* **Remediation:** Verify that `SlidingWindowDuplicateDetector` strictly enforces `duplicate_cache_max_elements` (50,000 items) and purges expired timestamps. Ensure large historical dataset queries in Phase 7 are chunked into windows $\le 30$ days.

### 2.4 Data Corruption, Sensor Synchronization & Timestamp Inconsistencies
* **Symptoms:** `SchemaValidationException` triggered in validation gate; `ClockDriftViolationException` rejecting packets $> \pm 5.0\text{s}$ into future or $> 24\text{h}$ into past; out-of-order timestamps arriving at normalizer.
* **Diagnostic Protocol:**
  1. Query Dead-Letter Queue (DLQ) memory records or disk JSON manifests (`/var/log/iob/dlq/`):
     ```bash
     find /var/log/iob/dlq -name "*.json" -mmin -60 | xargs cat
     ```
  2. Verify NTP / Chrony clock synchronization across industrial edge gateways and primary database host:
     ```bash
     chronyc sources -v
     ```
* **Remediation:** For clock skew events, enforce hardware NTP synchronization on PLC gateways. For out-of-order packets arriving within acceptable drift bounds ($< 60\text{s}$), rely on TimescaleDB hypertable `ORDER BY timestamp ASC` indexing during read-back.

---

## 3. Standard Root Cause Analysis (RCA) Framework

Whenever a Level 2 production anomaly impacts platform SLA, the Platform Owner mandates the completion of a formal Root Cause Analysis report within 48 hours using the following standardized template:

```markdown
# Root Cause Analysis (RCA) Report: [Incident ID]

**Incident Date:** YYYY-MM-DD  
**Severity:** P1 (Critical) / P2 (High) / P3 (Medium)  
**Lead Investigator:** Platform Owner / On-Call SRE  

### 1. Incident Summary
Brief executive summary describing what happened, duration of outage, and total telemetry frames dropped or delayed.

### 2. Timeline of Events (UTC)
* `HH:MM:SS` - First anomaly signal detected by monitoring framework.
* `HH:MM:SS` - Automated alert paged On-Call SRE.
* `HH:MM:SS` - Root cause isolated to [Component].
* `HH:MM:SS` - Mitigation applied; normal service restored.

### 3. Root Cause Investigation (Five Whys)
1. *Why did the ingestion pipeline stall?* Because connection handles to TimescaleDB exhausted.
2. *Why were connection handles exhausted?* Because an unindexed historical query locked pool threads.
3. *Why did the query lack an index?* Because a downstream ad-hoc query omitted `sensor_id` filter.
4. *Why did the query reach production?* Because query pagination guards were bypassed.
5. *Why were guards bypassed?* Because interface contract `IHistoricalQueryService` lacked strict query complexity timeouts.

### 4. Corrective & Preventive Action Plan (CAPA)
* **Immediate Fix:** Terminated blocking query queries via `pg_terminate_backend()`.
* **Preventive Action 1:** Enforce statement execution timeout (`statement_timeout = 5000ms`) on analytical database users.
* **Preventive Action 2:** Update `HistoricalQueryService` to enforce mandatory indexed compound keys.
```
