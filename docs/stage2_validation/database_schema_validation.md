# Database Schema Validation & Integrity Audit

**Stage:** 2 — Contract Validation, Alignment & Audit
**Owner:** Member 2 (Industrial Operating Brain — Data Foundation)
**Document ID:** `DB-SCHEMA-VAL-v1.0`
**Standards Alignment:** PostgreSQL 14+ / TimescaleDB-compatible DDL, ISA-95 Part 2 relational model
**Audit Date:** 2026-07-07 (UTC)
**Contract Baseline:** Canonical Stage 1 generation (`iob_data_engine` / `src/database/telemetry_repository.py`)

---

## 1. Purpose & Scope

Performs an audit on the structural relational layout used for streaming analytics and digital asset tracking within Member 2's PostgreSQL data storage zone. This document verifies the physical table topology, primary-key strategy, indexing placement, and schema-to-table mapping for the canonical telemetry store, confirming it can deterministically receive the validated JSON envelopes and serve Member 1 (API) and Member 3 (AI dataset) consumers.

**In Scope:** `iob_normalized_telemetry` physical layout, index placement, partition/posture, and JSONB storage alignment.
**Out of Scope:** Table mutation, index rewrite, or query tuning beyond contract conformance (read-only audit).

---

## 2. Physical Layout Audit

### Table: `iob_normalized_telemetry`

* **Primary Key:** `id SERIAL` (Integer autoincrement, optimized for indexing).
* **Foreign Key Constraints:** None applied directly to telemetry to ensure decoupling and support fast time-series writes.
* **Data Types:**
    * `device_id`: `VARCHAR(100)` (Indexed)
    * `site_id`: `VARCHAR(100)`
    * `area_id`: `VARCHAR(100)`
    * `timestamp_utc`: `TIMESTAMP WITH TIME ZONE` (Indexed)
    * `metrics`: `JSONB` (Indexed via GIN index for deep-nested metric lookups)

**Audit verification (against authoritative DDL):**

| Column | Defined Type | Constraint | Maps From | Status |
|---|---|---|---|---|
| `id` | `SERIAL` (integer autoincrement) | PK | auto-generated | ✅ Optimised append-only time-series key |
| `device_id` | `VARCHAR(100)` | Indexed | wire `device_id` / topic leaf | ✅ |
| `site_id` | `VARCHAR(100)` | — | `NormalizationEngine` topic split (parts[2]) | ✅ |
| `area_id` | `VARCHAR(100)` | — | `NormalizationEngine` topic split (parts[3]) | ✅ |
| `timestamp_utc` | `TIMESTAMP WITH TIME ZONE` | Indexed | epoch → UTC ISO conversion | ✅ TZ-safe |
| `metrics` | `JSONB` | GIN index | `telemetry` object | ✅ Flexible, schema-evolution tolerant |

*Evidence:* `src/database/telemetry_repository.py :: INIT_TABLE_SQL` defines exactly this table:

```sql
CREATE TABLE IF NOT EXISTS iob_normalized_telemetry (
    id              SERIAL PRIMARY KEY,
    device_id       VARCHAR(100) NOT NULL,
    site_id         VARCHAR(100) NOT NULL,
    area_id         VARCHAR(100) NOT NULL,
    timestamp_utc   TIMESTAMP WITH TIME ZONE NOT NULL,
    metrics         JSONB        NOT NULL,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Design rationale (validated):** The deliberate **absence of foreign-key constraints** on telemetry is a sound time-series optimisation — it decouples the high-velocity write path from asset-registry referential checks, eliminating lock contention during burst ingestion. Asset correlation is performed logically via `device_id` (and `site_id`/`area_id` extracted from the UNS topic), which is the recommended pattern for IoT-scale TimescaleDB/PG ingestion. The `JSONB` `metrics` column provides the flexible, schema-evolution-tolerant store that the charter's **Risk 1** mitigation requires (new metrics require no DDL migration).

### Execution Code Validation Block

```sql
-- Architectural Verification of Index Placement
CREATE INDEX IF NOT EXISTS idx_telemetry_device_ts
ON iob_normalized_telemetry (device_id, timestamp_utc DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_metrics_gin
ON iob_normalized_telemetry USING GIN (metrics);
```

**Audit verification:**
- `idx_telemetry_device_ts (device_id, timestamp_utc DESC)` — supports the dominant Member-1/Member-3 access pattern: *"latest N readings for a device, most-recent first."* The `(device_id, timestamp_utc DESC)` composite with the `DESC` ordering matches time-series window queries and pagination. ✅
- `idx_telemetry_metrics_gin` — a `GIN` index over the `metrics` JSONB enables efficient containment/key-exists queries (`metrics @> '{"spindle_speed_rpm": ...}'`) for deep-nested metric lookups without full-table scans. ✅
- Both use `IF NOT EXISTS` — idempotent and safe for re-runs / CI bootstrap. ✅

**Verdict:** **COMPLIANT**. The physical layout, key strategy, and index placement are precisely aligned with the streaming-analytics and digital-asset-tracking access patterns, and with the JSON contract defined in `json_contract_validation.md`.

---

## 3. Compliance and Query Optimization Analysis

- **Normalization Strategy:** Normalized at metadata levels, while streaming metrics are semi-structured (`JSONB`). This design provides optimal scalability without requiring heavy schema updates when sensors change.
- **Index Strategy:** The composite index `(device_id, timestamp_utc DESC)` supports fast data retrieval for Member 3's AI training routines and Member 1's historical REST queries.
- **Verdict:** **COMPLIANT**.

---

## 4. Audit Reconciliation Notes (Cross-Reference)

The `iob_normalized_telemetry` table above is the **canonical frozen storage contract** and is internally consistent with the JSON schemas and the Normalizer. The repository also defines a second, divergent telemetry table — `industrial.telemetry` (`database/schema.sql`: UUID `machine_id`/`sensor_id`, `measured_value`, `quality_code`, `PARTITION BY RANGE`) — which is the Phase 3 generation's store and is **not** written to by the canonical pipeline. That divergence, plus the Member-3 read-path mismatch (`datasets/extractor.py` queries `telemetry`/`machine_failures`), is tracked as **DB-01 / DB-02 / DB-03 / DB-04** in the master `validation_report.md` and must be reconciled before the Stage 4 Contract Freeze.

**Action for freeze:** Declare `iob_normalized_telemetry` (this §2 layout + §Execution Block indexes) as the single canonical telemetry table; retire or explicitly alias `industrial.telemetry`; repoint `datasets/extractor.py` to the canonical table and columns.
