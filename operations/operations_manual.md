# IOB Core Operations Manual

**Status:** `PRODUCTION-APPROVED`

## 1. System Runtime Configuration
The Industrial Operating Brain ingestion engine runs inside an isolated network cluster. Configuration parameters are loaded dynamically from environment files without using hardcoded defaults.

### Core Environment Variable References
* `IOB_DATABASE_URL`: Connection string for the underlying PostgreSQL/TimescaleDB data warehouse instance.
* `IOB_MQTT_BROKER_URL`: Address of the primary EMQX messaging node (`mqtt://iob-emqx-backbone:1883`).
* `IOB_INGEST_LOG_LEVEL`: Determines logging verbosity across worker threads (`INFO`, `WARNING`, `ERROR`).

## 2. Infrastructure Step-by-Step Management Procedures

### Step-by-Step System Startup Procedure
Execute this sequence to safely initialize the network fabric and database layers:
1. Initialize the internal cluster network: `docker network create iob-industrial-backbone-network`
2. Start the storage tier container and wait for initialization scripts to finish: `docker start iob-timescaledb-cluster`
3. Verify that database storage engines are healthy: `docker exec -it iob-timescaledb-cluster pg_isready -U iob_platform_admin`
4. Initialize the messaging fabric container: `docker start iob-emqx-backbone`
5. Start the pipeline ingestion processing workers: `docker start iob-ingestion-subscriber`

### Step-by-Step System Shutdown Procedure
Execute this sequence during maintenance windows to prevent data corruption or interrupted write transactions:
1. Stop the ingestion subscriber workers to gracefully halt incoming data streams: `docker stop iob-ingestion-subscriber`
2. Stop the core EMQX message broker node: `docker stop iob-emqx-backbone`
3. Flush any pending memory transactions to disk and stop the database container: `docker stop iob-timescaledb-cluster`

## 3. Log Locations & Health Check Diagnostics
* **Ingestion Pipeline Logs:** Ingestion workers output runtime data directly to `/var/log/iob/pipeline_engine.json`. Logs use a structured JSON format to simplify tracking across external search systems.
* **Automated Health Checks:** Use the system diagnostic ping command to verify connection paths and pipeline responsiveness: `docker exec -it iob-ingestion-subscriber python -c "from integration.health import run_ping; run_ping()"`
