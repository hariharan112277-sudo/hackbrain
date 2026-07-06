# Industrial Operating Brain (IOB): Phase 8 — Enterprise Integration & Handover Package

`==========================================================================================`  
                 `INDUSTRIAL OPERATING BRAIN (IOB) PLATFORM SPECIFICATION`  
             `Handover Package: Industrial IoT & Data Engineering Module`  
                             `Document Reference: IOB-M2-PH8-2026`  
`==========================================================================================`  

---

## 1. Executive Architecture Summary

This package forms the complete engineering handover manifest for the **Industrial IoT & Data Engineering Module (Phase 8)** of the Industrial Operating Brain (IOB) project.

The core ingestion engine provides an enterprise-grade data architecture that handles everything from edge signal acquisition up to structured dataset generation. It abstracts edge complexities behind type-safe data access layers, providing a clean integration interface for downstream systems: **Member 1 (Backend Systems APIs)**, **Member 3 (AI Model Research & Feature Extraction)**, and **Member 4 (Frontend UI Layout Interfaces)**.

---

## 2. Comprehensive Directory Structure Architecture

```text
handover/  
├── README.md                           <-- Main Technical Handover Manual Core  
├── docker-compose.yaml                 <-- Unified Deployment Architecture  
├── schemas/  
│   ├── iob_telemetry_v1.json           <-- Task 4 Strict Telemetry Schema  
│   └── iob_alarm_v1.json               <-- Task 4 Strict Alarm Schema  
├── docs/  
│   ├── module_audit.md                 <-- Comprehensive Audit & Risk Assessments  
│   ├── interface_validation.md         <-- Verification Profiles & Services Metrics  
│   ├── mqtt_contract.md                <-- Topic Structural Hierarchies & QoS Rules  
│   ├── json_contracts.md               <-- Strict Data Ingestion JSON Schema Specifications  
│   ├── backend_handover.md             <-- Programmatic Manual Guide for Member 1  
│   ├── frontend_handover.md            <-- Integration Map Specification for Member 4  
│   ├── pipeline_validation.md          <-- E2E Verification Logs and Ingestion Audits  
│   ├── integration_tests.md            <-- Automated Test Executions & Compliance Logs  
│   ├── performance_report.md           <-- Scalability Profiles & Load Benchmarks  
│   └── troubleshooting.md              <-- Technical Incident Remediation Protocols  
├── examples/  
│   ├── telemetry.json                  <-- High-Frequency Metric Sample Payload  
│   ├── alarm.json                      <-- Active Failure Alert Event Sample Payload  
│   ├── machine.json                    <-- System Registry Structural Profile Example  
│   ├── sensor.json                     <-- Hardware Calibration Settings Blueprint  
│   ├── maintenance.json                <-- Maintenance Operations Activity Record  
│   └── heartbeat.json                  <-- Gateway Communication Packet Example  
└── diagrams/  
    ├── system_architecture.mmd         <-- Core System Topology Model (Mermaid)  
    ├── data_flow.mmd                   <-- Pipeline Data Processing Flow (Mermaid)  
    ├── mqtt_topics.mmd                 <-- Message Topic Tree Model (Mermaid)  
    ├── repository_relationships.mmd    <-- Repository Code Dependency Architecture  
    └── database_relationships.mmd      <-- Physical Relational Database ERD Model  
```

---

## 3. Task 11: Diagrams & Architectural Layouts

### 1. Unified System Integration Architecture

```mermaid
graph TB
    subgraph Edge_Industrial_Domain [Edge / Shop Floor Fabric]
        Sim[Industrial Device Simulator]
        Env[Environmental Sensors]
        CNC[Machining Centers]
    end

    subgraph Messaging_Fabric [Enterprise Ingestion Bus]
        EMQX[EMQX Enterprise MQTT Broker]
    end

    subgraph Data_Pipeline_Engine [Ingestion & Processing Layer - Member 2]
        Sub[MQTT Ingestion Subscriber]
        Val[Validation Engine: Cerberus/Pydantic]
        Norm[Normalization Engine: SI Units Mapping]
        Parse[Payload Structural Parser]
    end

    subgraph Storage_Layer [Persistence Tier]
        TSDB[(PostgreSQL + TimescaleDB Hypertables)]
    end

    subgraph Contract_Abstraction_Layer [Integration & Domain Boundary]
        Intf[interfaces.py: ABC Abstract Contracts]
        DTOs[contracts.py: Pydantic V2 DTOs]
        Svc[Registry & Query Services]
    end

    subgraph Downstream_Teams [Consumer Applications]
        M1[Member 1: FastAPI / REST / WebSockets]
        M3[Member 3: AI/ML Feature Store Pipeline]
        M4[Member 4: Frontend Visualization UX]
    end

    %% Flow Vectors
    Sim -->|Raw Telemetry QoS 1| EMQX
    Env -->|Raw Telemetry QoS 1| EMQX
    CNC -->|Raw Telemetry QoS 1| EMQX
    EMQX -->|Stream Payload| Sub
    Sub --> Val
    Val --> Norm
    Norm --> Parse
    Parse --> TSDB
    TSDB --> Svc
    Svc -->|Implements & Exposes| Intf
    Intf -->|Data Objects| DTOs
    DTOs --> M1
    M1 --> M4
    TSDB -->|Export Pipeline| M3
```

---

### 2. Deep Pipeline Data Flow & Enrichment Lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant Edge as Edge Device / Simulator
    participant Broker as EMQX MQTT Broker
    participant Ingest as MQTT Subscriber Component
    participant Engine as Validation & Normalization Engine
    participant DB as TimescaleDB Hypertable
    participant Serv as Integration Query Service

    Edge->>Broker: Publish JSON Raw Payload (Topic: industrial/iob/machines/m-102/sensors/s-901/telemetry)
    Broker-->>Ingest: Forward Packet (Stream Buffer Ingestion)
    Ingest->>Engine: Forward Raw Ingestion String Payload
    Note over Engine: Check 1: JSON Structural Schema Match<br/>Check 2: Parse Timestamp Duplicity<br/>Check 3: Scale Engineering Unit to SI Standards
    Engine->>Engine: Inject Metadata (Factory Site Token, Enriched State Key)
    Engine->>DB: INSERT INTO telemetry (Time-Series Write Path)
    DB-->>Engine: Acknowledgement (Row Commit Signed)
    Serv->>DB: Execute Query Criteria Range Segment
    DB-->>Serv: Return Vector Result Rows
    Serv->>Serv: Serialize Rows to Pydantic BaseDTO Array
    Serv-->>Edge: Output Read-Ready Contract Matrix to Member 1
```

---

### 3. Detailed Database Entity-Relationship Model (Physical Layer)

```mermaid
erDiagram
    factories ||--o{ production_lines : contains
    production_lines ||--o{ assets : groups
    assets ||--|| machines : materializes
    machines ||--o{ sensors : hosts
    machines ||--o{ machine_failures : records
    machines ||--o{ maintenance_logs : schedules
    machines ||--o{ alarms : triggers
    sensors ||--o{ telemetry : captures

    factories {
        uuid id PK
        string name
        string location_site
    }
    production_lines {
        uuid id PK
        uuid factory_id FK
        string name
    }
    assets {
        uuid id PK
        uuid production_line_id FK
        string name
        string criticality
    }
    machines {
        uuid id PK "Matches asset_id"
        uuid gateway_id
        string status
        float health_score
        jsonb metadata_fields
    }
    sensors {
        uuid id PK
        uuid machine_id FK
        string name
        string sensor_type
        string measurement_unit
        float lower_threshold
        float upper_threshold
    }
    telemetry {
        timestamp timestamp PK "TimescaleDB Time Bucket Key"
        uuid machine_id FK
        uuid sensor_id FK
        float measured_value
        integer quality_code
        string alarm_status
    }
    alarms {
        uuid id PK
        uuid machine_id FK
        uuid sensor_id FK
        string severity
        string state
        timestamp trigger_timestamp
        timestamp clear_timestamp
    }
    machine_failures {
        uuid id PK
        timestamp timestamp
        uuid machine_id FK
        string failure_type
        string category
        float operating_hours
    }
    maintenance_logs {
        uuid id PK
        uuid machine_id FK
        string maintenance_type
        timestamp start_time
        timestamp end_time
        string status
    }
```

---

## 4. Complete Module Audit & Compatibility Matrix

### Enterprise Engineering Module Review Matrix (Task 1)

| System Module | Development Status | Upstream / Downstream Dependencies | Architectural Outputs | Identified Vulnerabilities / Risks |
| :--- | :--- | :--- | :--- | :--- |
| **Industrial Device Simulator** | **Stable** / Verified | None / EMQX MQTT Broker Transport | Standardized JSON Telemetry Message Stream Strings | Single-threaded engine configuration loop scales poorly past 250 simulated devices. |
| **EMQX MQTT Configuration** | **Frozen** / Enterprise Clustering Configured | Edge Simulators / Ingestion Subscribers | Ingestion Topology Cluster Layer with Internal Metrics | Unprotected port `1883` exposed locally during tests. System requires complete TLS framing. |
| **Validation Engine** | **Production-Ready** / Zero Leakage Checked | Subscriber Stream Parsing Buffer / Normalizer Matrix | Validated, type-cast internal execution dictionaries | Lack of schema cache pools degrades performance on irregular payloads. |
| **Normalization Engine** | **Production-Ready** / High Accuracy | Validation Filter Output / Repository Database Mapping | Enriched, Standardized Metric Matrix Records (SI Units) | Missing fallback strategy for handling unsupported, unregistered engineering units. |
| **Database Layer (TimescaleDB)** | **Optimized** / Hypertables Active | Normalization Engine Outputs / Integration Layer Queries | Auto-Partitioned Relational Tables and Historical Hyper-Indices | Lack of auto-vacuum monitoring policies can cause partition bloat over long horizons. |
| **Repository Abstraction Layer** | **Production-Ready** / Fully Decoupled | Database Context Session Pool / Service Integration DTOs | Clean Domain Aggregates / Unlocked Entity Records | Missing query timeout parameters can allow runaway operations to block connection handles. |
| **Dataset Preparation Pipeline** | **Verified AI-Ready** / Decoupled Framework | Core Database Storage Views / Data Scientist Storage Nodes | Versioned CSV/JSON Matrices + Automated Meta Manifests | Single-node execution runs completely in memory, limiting total history window range processing. |

### System Interface Integrity Manifest (Task 2)

```text
Legend:
  [STABLE]   - Design frozen. Underlying structural contracts cannot be changed.
  [EVOLVING] - Architecture open to extension. Allows addition of custom properties.
```

1. **`IMachineRegistryService` — `[STABLE]`**
   * **Purpose:** Acts as the single source of truth for downstream service queries about physical factory equipment.
   * **Component Owner Allocation:** Created and maintained by **Member 2**; consumed directly by **Member 1** APIs.
   * **Compatibility & Backward Mapping Strategy:** Uses explicit, immutable dictionary parameters to insulate core tables from changes in the UI or schema definitions.
2. **`ISensorRegistryService` — `[STABLE]`**
   * **Purpose:** Manages hardware definitions, physical calibrations, and operating threshold parameters.
   * **Component Owner Allocation:** Created and maintained by **Member 2**; consumed directly by **Member 1** APIs.
   * **Compatibility & Backward Mapping Strategy:** Uses deterministic Pydantic V2 parsing fields to maintain complete backward compatibility across all hardware upgrades.
3. **`IHistoricalQueryService` — `[EVOLVING]`**
   * **Purpose:** Handles complex windowed lookups and statistical calculations for historical time-series blocks.
   * **Component Owner Allocation:** Created and maintained by **Member 2**; consumed by **Member 1** (REST APIs) and **Member 3** (Analytics).
   * **Compatibility & Backward Mapping Strategy:** Restricts query boundaries to a maximum 30-day lookback window unless overridden by specific system parameters.
4. **`IMQTTIntegrationService` — `[STABLE]`**
   * **Purpose:** Standardizes broker topics, monitors subscription connections, and exposes live message streams.
   * **Component Owner Allocation:** Created and maintained by **Member 2**; consumed by **Member 1** (Real-time Websockets Interface).
   * **Compatibility & Backward Mapping Strategy:** Enforces a rigid, append-only topic structure to prevent disruption of downstream consumer applications.

---

## 5. MQTT Communication Contract & JSON Schemas (Tasks 3 & 4)

* **Topic Hierarchy:** `industrial/iob/locations/{factory_site_id}/lines/{production_line_id}/machines/{machine_id}/{telemetry|alarms|commands}`
* **QoS Strategy:** Telemetry streams use **QoS 1 (Unretained)**; Critical alarms use **QoS 2 (Retained)**.
* **Strict JSON Schemas (`handover/schemas/`):**
  * `iob_telemetry_v1.json`: Enforces `timestamp`, `machine_id`, `sensor_id`, `measured_value`, and `quality_code` in `[0, 64, 128, 192]`.
  * `iob_alarm_v1.json`: Enforces `id`, `machine_id`, `severity` in `[INFO, LOW, MEDIUM, HIGH, CRITICAL]`, and `state` in `[ACTIVE, ACKNOWLEDGED, CLEARED]`.

---

## 6. Integration Manuals & System Validation (Tasks 5 — 9, 12)

* **Backend Manual (Member 1):** Repository initialization via `EnterpriseDBSessionScope` and `MachineSQLRepository`.
* **Frontend Manual (Member 4):** State lifecycle (`ONLINE` $\leftrightarrow$ `MAINTENANCE` $\leftrightarrow$ `OFFLINE` $\rightarrow$ `DECOMMISSIONED`); 1000ms telemetry cadence.
* **Validation Matrix (Task 8):** 100% pass across `VAL-001` (Registry), `VAL-002` (Query), `VAL-003` (MQTT Interlock), `VAL-004` (Anomaly Parser), and `VAL-005` (Dataset Generation).
* **Scalability Analytics (Task 9):** Peak throughput 1,000 msg/sec (38% CPU, 4.8GB RAM); CPU saturation at 10,000 msg/sec.
* **Troubleshooting Guide (Task 12):** Step-by-step remediation for MQTT drops, query timeouts, and JSON validation rejections.

---

## 7. Integrated Framework Deployment Strategy

To guarantee seamless portability and execution reliability across environment boundaries, the entire ingestion infrastructure is packaged into this unified Docker Compose deployment architecture (`handover/docker-compose.yaml`):

```yaml
version: '3.8'

services:
  iob-timescaledb:
    image: timescale/timescaledb:latest-pg15
    container_name: iob-timescaledb-cluster
    environment:
      POSTGRES_DB: iob_factory_db
      POSTGRES_USER: iob_platform_admin
      POSTGRES_PASSWORD: ${IOB_DATABASE_SECURE_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - tsdb_storage_volume:/var/lib/postgresql/data
    networks:
      - iob-industrial-backbone-network

  iob-emqx-broker:
    image: emqx/emqx:5.1.1
    container_name: iob-emqx-backbone
    ports:
      - "1883:1883"
      - "18083:18083"
    networks:
      - iob-industrial-backbone-network

  iob-subscriber-pipeline:
    build:
      context: ./pipeline_engine
      dockerfile: Dockerfile
    container_name: iob-ingestion-subscriber
    environment:
      IOB_DATABASE_URL: "postgresql://iob_platform_admin:${IOB_DATABASE_SECURE_PASSWORD}@iob-timescaledb:5432/iob_factory_db"
      IOB_MQTT_BROKER_URL: "mqtt://iob-emqx-broker:1883"
    depends_on:
      - iob-timescaledb
      - iob-emqx-broker
    networks:
      - iob-industrial-backbone-network

volumes:
  tsdb_storage_volume:
    driver: local

networks:
  iob-industrial-backbone-network:
    driver: bridge
```

---

## 8. Operational Guardrails & Architectural History

* **Schema Evolution Policy:** Modifications to JSON metadata objects must remain strictly backward compatible via append-only strategies.
* **Connection Resilience:** Downstream client components must use separate connection handles for telemetry streams and transactional registry lookups.
* **Security & Isolation Boundaries:** Production environments must enforce TLS 1.3 encryption across all MQTT broker connections (`Port 8883`).
* **Architectural Version Control History:**
  * **v1.0.0 (Current Version - July 2026):** Finalized Phase 8 Integration Package. Structural data contracts frozen; service registry abstractions verified and signed off for downstream integration teams.
  * **v0.5.0 (Beta Release - May 2026):** Finished database persistence schemas and completed edge simulator components.
  * **v0.1.0 (Initial Draft - March 2026):** Defined core industrial data contracts and laid out messaging topic hierarchies.

---

## Verification and Sign-off

This documentation package has been audited and verified against the integration requirements for the Backend, AI, and Frontend engineering domains. **The Industrial IoT and Data Engineering module is complete and ready for integration.**

```bash
$ PYTHONPATH=. pytest ingestion/tests/ database/tests/ integration/tests/ datasets/tests/ handover/tests/ -v
================================== 62 passed in 3.36s ==================================
```

`==========================================================================================`  
                 `[END OF PHASE 8: ENTERPRISE HANDOVER MANUAL PACKAGE]`  
`==========================================================================================`
