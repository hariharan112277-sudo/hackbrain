# Telemetry Architecture & Data Ingestion Flow

### 1. End-to-End Data Pipeline Architecture

```
[ Industrial Device Simulator ]
            │
            │ (MQTT Protocol over TLS / JSON Payload)
            ▼
[ MQTT Broker: Unified Namespace ]
            │
            │ (Deterministic Topic Subscription)
            ▼
[ Subscriber Node & Validation Engine ] ──(Drops Corrupt Frames)──> [ Error Log ]
            │
            │ (Parses / Normalizes / Types Casts)
            ▼
[ Repository Access Layer ]
            │
            │ (SQL Write Operations / Prepared Batch Inserts)
            ▼
[ PostgreSQL Industrial Database ]
```

### 2. Pipeline Execution Steps

#### Step 1: High Frequency Edge Sampling
The physical device Layer reads sensors natively. The edge node packs current frames into a JSON payload structure containing an explicit UNIX epoch microsecond timestamp, avoiding field drifting.

#### Step 2: Unified Namespace (UNS) Publishing
Payloads publish to an explicit topic structure:
`IOB_GLOBAL/CAPS_01/PAD_02/MAL_05/MC_CNC_01_A/telemetry`

#### Step 3: Subscriber Containment & Validation
The Subscriber handles incoming byte arrays. It acts as a gatekeeper using structural assertions:
1. **Structural Sufficiency**: Assures presence of timestamp, asset_id, and metrics blocks.
2. **Type Coercion**: Foractively enforces casting incoming values to double-precision floats (float8).
3. **Boundary Assessment**: Checks metrics against physical maximums (e.g., negative currents are dropped instantly as validation failures).

#### Step 4: Normalization & Standardization
Timestamps translate cleanly into standard ISO 8601 strings with timezone parameters fixed to UTC. Metric names resolve uniformly across vendor types (e.g., temp_in_celsius normalizes cleanly into core_temperature).

#### Step 5: Database Repository Mapping
The normalized objects route through the repository pattern layer. The layer issues optimized INSERT INTO telemetry_store execution blocks utilizing batched transactions to optimize high-volume disk-write operations.

### Integration with hackbrain repo
This telemetry pipeline aligns with existing MQTT/UNS wiring and repository patterns already present in the project.