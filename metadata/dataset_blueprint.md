# Integrated Dataset Blueprints & Unified Feature Dictionary

This blueprint provides the exact data schema definitions without instantiating mock data, remaining fully compliant with your frozen validation rules.

### 1. Master Feature Dictionary

| Target Feature Name | Data Type | Engineering Units | Validation Constraint Rules | Physical System Correspondence |
| :--- | :--- | :--- | :--- | :--- |
| timestamp | TIMESTAMPZ | ISO 8601 UTC | Must be past or present; microsecond resolution | System Log Clock |
| asset_id | VARCHAR(64) | N/A | Must match active device inventory | Physical Asset Tag |
| vibration_rms | FLOAT8 | $m/s^2$ | Value must be $\ge 0.0$ and $\le 500.0$ | Accelerometer Output |
| core_temp | FLOAT8 | °C | Value must be $\ge -50.0$ and $\le 1000.0$ | Core Thermocouple |
| drive_current | FLOAT8 | A | Value must be $\ge 0.0$ and $\le 250.0$ | CT Transformer |
| machine_state | VARCHAR(32)| N/A | Must equal a valid PackML string literal | Controller Logic Block |

### 2. Unified Dataset Inter-Relationships

```
[ metadata_dataset ]
         │
         ├──(1 : N)──> [ telemetry_dataset ] (Linked via asset_id)
         │
         ├──(1 : N)──> [ alarm_dataset ]     (Linked via asset_id)
         │
         └──(1 : N)──> [ maintenance_dataset ](Linked via asset_id)
```

### 3. Downstream Consumer Target Readiness Matrix
- **Member 3 (AI / GraphRAG)**: The relational foreign key linkages between asset_id fields inside telemetry_dataset and rows within alarm_dataset allow the Graph builder to programmatically link structural anomalies to real mechanical breakdowns.
- **Member 4 (Frontend UI)**: Pre-aggregated time-bucket windows assure rapid multi-scale dashboard loading speeds without overloading memory lanes.

### Integration with hackbrain repo
Dataset schemas and relationships are ready for immediate use by existing GraphRAG and UI layers.