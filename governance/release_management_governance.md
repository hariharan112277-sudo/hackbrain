# Platform Release Management & Lifecycle Governance

**Platform:** Industrial Operating Brain (IOB)  
**Document Owner:** Principal Industrial IoT Platform Owner  
**Standard Compliance:** ITIL Release & Deployment Management

---

## 1. Official Release Notes Template

Every scheduled release must publish standardized release documentation:

```markdown
# IOB Platform Release Notes: Version [Major.Minor.Patch]
**Release Date:** YYYY-MM-DD  
**Release Authority:** Principal Industrial IoT Platform Owner  

### 1. Overview & Scope
Summary of features, infrastructure enhancements, and defect fixes included in this release.

### 2. New Features & Improvements
* [CHG-2026-001] Native OPC-UA hardware gateway connector support.

### 3. Defect Fixes
* [INC-20260703-001] Patched Z-score outlier removal handling of OPC quality code 64 null values.

### 4. Breaking Changes & Deprecations
* None in this release. (All schemas adhere to append-only backward compatibility).

### 5. Known Issues
* Single-threaded Python subscriber experiences CPU saturation under synthetic 10,000 msg/sec load bursts.

### 6. Migration & Deployment Guide
1. Pull latest Docker container artifacts: `docker pull iob-ingestion-subscriber:v1.1.0`.
2. Apply Alembic non-blocking schema migration: `alembic upgrade head`.
3. Perform rolling restart of consumer pods.

### 7. Automated Rollback Plan
If validation gates fail post-deployment:
1. Revert container tag to previous stable version: `docker tag iob-ingestion-subscriber:v1.0.0`.
2. Re-run automated health checks: `pytest phase10/archive/tests/test_pipeline_stages.py -v`.
```

---

## 2. Zero-Downtime Blue/Green Deployment & Rollback Protocol

To ensure continuous factory floor operations during upgrades:
1. **Blue (Current Production):** Active subscriber cluster consuming from `industrial/iob/...`.
2. **Green (Target Upgrade):** Deploy new version alongside Blue cluster with shared read-only database connections.
3. **Traffic Cutover:** Switch MQTT subscriber consumer group bindings from Blue to Green.
4. **Verification Gate:** Monitor Green cluster error rates for 15 minutes. If validation rejections exceed 0.1%, execute instant cutover back to Blue consumer group.
