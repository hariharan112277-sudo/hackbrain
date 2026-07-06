# Disaster Recovery Blueprint

**Target Matrix:** `RTO < 15 Minutes, RPO < 5 Minutes`

```text
                                  [Disaster Event Identified]  
                                               │  
                      ┌────────────────────────┴────────────────────────┐  
                      ▼                                                 ▼  
          [Database Core Failure]                            [MQTT Messaging Outage]  
                      │                                                 │  
   1. Stop Ingestion Subscriber Workers              1. Inspect Local Connection Logs  
   2. Deploy Target Container Image Replica          2. Check Client Security Token Access  
   3. Restore Snapshot via Point-in-Time             3. Reinitialize Container Services  
                      │                                                 │  
                      └────────────────────────┬────────────────────────┘  
                                               ▼  
                         [Run Automated Pipeline Validation Tests]  
                                               │  
                         [Resume Production Processing Operations]  
```

## Recovery Procedures

### 1. Recovering From Storage Tier Failures (Database Offline)
1. Stop the ingestion subscriber workers to prevent network timeouts or dropped connection attempts.
2. Spin up a clean replica database container using your primary infrastructure configurations.
3. Restore your latest transaction log snapshot using standard point-in-time recovery tools:
   ```bash
   pg_restore -v -h localhost -U iob_platform_admin -d iob_factory_db /var/backups/iob/tsdb_snapshot_latest.dump
   ```
4. Restart the data ingestion workers and verify transaction logs to ensure normal processing has resumed.

### 2. Recovering From Data Ingestion Disruptions (MQTT Broker Outage)
1. Check the local subscription worker connection logs to pinpoint network disconnect root causes.
2. Verify client authentication and access tokens against the parameters defined in your broker security rules.
3. Reinitialize the messaging container service to reset its network stack and routing configurations: `docker restart iob-emqx-backbone`.

### 3. Verifying System Health After Recovery
After completing any recovery procedure, run the end-to-end integration test suite to verify pipeline connectivity, data accuracy, and schema enforcement:
```bash
pytest phase10/archive/tests/test_pipeline_stages.py -v
```
