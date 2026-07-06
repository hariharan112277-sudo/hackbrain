# Preventive Maintenance Documentation

**Maintenance Interval:** `Monthly Scheduled Operations`

## 1. Database Index & Partition Optimizations

To keep historical query speeds fast, run the following partition check and cleanup commands on the first Sunday of every month:

```sql
-- Analyze time-series hypertable layouts and index health parameters
SELECT * FROM timescaledb_information.hypertables;

-- Force a manual cleanup sweep across database table spaces to free unallocated disk sectors
VACUUM ANALYZE telemetry;

-- Reindex high-frequency tracking records to maintain fast search operations
REINDEX TABLE telemetry;
```

## 2. Log Rotation Rules

Log files are managed by system services to prevent disk space issues on host machines. Ensure your system configurations match these parameters:

```text
/var/log/iob/*.json {
    daily
    rotate 14
    missingok
    notifempty
    compress
    sharedscripts
    postrotate
        docker kill --signal=SIGUSR1 iob-ingestion-subscriber > /dev/null 2>&1
    endscript
}
```

## 3. Cold Data Storage Archival Routines

Time-series data older than 90 days must be migrated from high-speed local NVMe drives to cheaper, long-term cold storage nodes. Run this pipeline script during scheduled maintenance windows to compress and move older partitions without interrupting live ingestion streams:

```bash
python -m tasks.archive_cold_partitions --before_days=90 --target_s3_bucket="s3://iob-cold-storage-archive/"
```
