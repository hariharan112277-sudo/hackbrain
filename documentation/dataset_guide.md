# Integrated Dataset Architecture & Mapping Manual

### 1. Structural Overview
The Stage 3B Data Package delivers an interconnected web of relational tables and stream formats. These assets provide a clean data foundation that allows the backend and frontend components to function smoothly without violating frozen schema contracts.

### 2. Comprehensive Relational Map
*   machine_metadata.json lists the master asset definitions.
*   telemetry_historical.csv maps directly to machine_metadata.json via the asset_id foreign key.
*   alarm_dataset.json references telemetry trends via a joint lookup using machine_id and the explicit event timestamp.
*   maintenance_history.json maps directly to alarm_dataset.json through the triggered_by_alarm tracking key.

### 3. Core Functional Interfaces

```
[ machine_metadata ] ──(1:N)──> [ telemetry_historical ]
         │
         └──(1:N)──> [ alarm_dataset ] ◄──┘
                     │
                     └──(1:1)──> [ maintenance_history ]
```

### 4. Downstream Engineering Guidance
*   **Member 1 (Backend REST Delivery):** These dataset files can be directly loaded into test frameworks using standard database seeding patterns (psql -c "\copy ..."), bypassing the need to wait for real-world edge hardware integrations.
*   **Member 3 (AI Model Training & Knowledge Graph Construction):** The deliberate overlap between anomalous telemetry spikes and corresponding alarm entries provides a clean training set for training failure prediction models and constructing GraphRAG nodes.

### Integration with hackbrain repo
All relationships and interfaces respect existing wiring and frozen contracts.