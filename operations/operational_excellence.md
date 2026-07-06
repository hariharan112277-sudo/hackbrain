# Platform Operational Excellence & SRE Runbook Registry

**Platform:** Industrial Operating Brain (IOB)  
**Document Owner:** Principal Industrial IoT Platform Owner  
**Standard Compliance:** Site Reliability Engineering (SRE) Best Practices

---

## 1. Core Operations & Maintenance Runbook Registry

To ensure consistent execution across site reliability teams, all operational procedures are codified into standardized runbooks:

| Runbook ID | Title | Execution Trigger | Primary Execution Steps | Target SLA |
| :--- | :--- | :--- | :--- | :--- |
| **SRE-RUN-001** | Standard System Startup & Initialization | Cluster bootstrap or maintenance recovery | `docker network create` $\rightarrow$ start `iob-timescaledb-cluster` $\rightarrow$ verify `pg_isready` $\rightarrow$ start `iob-emqx-backbone` $\rightarrow$ start `iob-ingestion-subscriber`. | $< 3$ Minutes |
| **SRE-RUN-002** | Graceful System Shutdown & Drain | Scheduled patch or OS kernel upgrade | Stop `iob-ingestion-subscriber` $\rightarrow$ flush inflight queues $\rightarrow$ stop `iob-emqx-backbone` $\rightarrow$ checkpoint DB $\rightarrow$ stop `iob-timescaledb-cluster`. | $< 5$ Minutes |
| **SRE-RUN-003** | Monthly TimescaleDB Hypertable Maintenance | First Sunday of every month at 02:00 UTC | Execute `VACUUM ANALYZE telemetry;` and `REINDEX TABLE telemetry;` across active chunks. | Non-blocking |
| **SRE-RUN-004** | Cold Data Partition Archival | First Saturday of every month at 01:00 UTC | Execute `python -m tasks.archive_cold_partitions --before_days=90 --target_s3_bucket=...` | $< 2$ Hours |

---

## 2. Automated Backup & Disaster Recovery Runbook

### 2.1 Daily Automated Point-in-Time Snapshot Protocol
The storage engine executes automated binary snapshots via `pg_dump` and Write-Ahead Log (WAL) archiving every 24 hours at 00:00 UTC:
```bash
#!/usr/bin/env bash
# SRE Daily Backup Script
BACKUP_TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
SNAPSHOT_FILE="/var/backups/iob/tsdb_snapshot_${BACKUP_TIMESTAMP}.dump"

docker exec -t iob-timescaledb-cluster pg_dump -Fc -U iob_platform_admin -d iob_factory_db > "${SNAPSHOT_FILE}"
aws s3 cp "${SNAPSHOT_FILE}" s3://iob-enterprise-backups-secure/daily/
```

### 2.2 Disaster Recovery Rollback Procedure (`RTO < 15m, RPO < 5m`)
1. **Isolate Ingestion:** Immediately halt ingestion workers (`docker stop iob-ingestion-subscriber`) to prevent split-brain writes.
2. **Provision Fresh Instance:** Deploy clean TimescaleDB cluster container using `docker-compose.yaml`.
3. **Restore Verified Dump:**
   ```bash
   pg_restore -v -h localhost -U iob_platform_admin -d iob_factory_db /var/backups/iob/tsdb_snapshot_latest.dump
   ```
4. **Execute Post-Recovery Verification Gate:**
   ```bash
   PYTHONPATH=. pytest phase10/archive/tests/test_pipeline_stages.py -v
   ```
5. **Resume Ingestion:** Start ingestion workers and monitor EMQX connection drain.

---

## 3. Production Alerting & Prometheus KPI Thresholds

```yaml
groups:
  - name: iob_platform_alerts
    rules:
      - alert: EMQXBrokerClientDisconnections
        expr: increase(emqx_client_disconnected_count[1m]) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High MQTT client disconnect rate detected on EMQX backbone."
          
      - alert: TelemetryProcessingLatencyHigh
        expr: histogram_quantile(0.95, sum(rate(iob_pipeline_processing_duration_ms_bucket[5m])) by (le)) > 100
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "P95 telemetry processing latency exceeded 100ms envelope."

      - alert: DatabasePoolExhaustionWarning
        expr: iob_db_pool_active_connections / iob_db_pool_total_size > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "TimescaleDB connection pool active sessions above 85% capacity."
```
