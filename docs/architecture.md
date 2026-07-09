# Industrial Operating Brain (IOB): Phase 4 — Industrial Telemetry Ingestion Pipeline

**Document Version:** 1.0.0-INGEST  
**Classification:** Operational Technology (OT) Edge Processing Software Component  
**Standard Compliance:** ISA-95 Part 2, IEC 62443, ISO/IEC 20922 (MQTT 5.0), RFC 8259 (JSON)

---

## 1. System Engineering Architecture

Phase 4 defines the data validation, enrichment, and normalization layer for the Industrial Operating Brain (IOB). It processes asynchronous raw data streams from the EMQX Message Bus and outputs strongly typed, clean Python data structures to downstream storage engines.

### 1.1 Linear Pipeline Processing Stages

```mermaid
graph TD
    classDef broker fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef stage fill:#e8f5e9,stroke:#388e3c,stroke-width:1px;
    classDef interface fill:#fff3e0,stroke:#f57c00,stroke-width:2px;

    EMQX[EMQX MQTT Broker Node] :::broker -->|Asynchronous Delivery| SUB[subscriber.py: MqttTelemetrySubscriber] :::stage
    SUB -->|Buffer Push| PL[pipeline.py: TelemetryProcessingPipeline] :::stage

    subgraph Execution Processing Array [In-Memory Validation Chain]
        PL --> V_JSON[validator.py: JsonPayloadValidator] :::stage
        V_JSON --> V_TS[timestamp_validator.py: ChronoTimestampValidator] :::stage
        V_TS --> V_DUP[duplicate_detector.py: SlidingWindowDuplicateDetector] :::stage
        V_DUP --> V_QUAL[quality_checker.py: OperationalQualityChecker] :::stage
        V_QUAL --> NORM[normalizer.py: EngineeringUnitNormalizer] :::stage
        NORM --> ENRICH[metadata_enricher.py: StaticAssetMetadataEnricher] :::stage
        ENRICH --> PARSE[parser.py: TelemetryObjectParser] :::stage
    end

    PARSE -->|Clean Data Model Structure| DISP[dispatcher.py: EventDispatcher] :::stage
    DISP -->|Dependency Injection Call| DB_INT[interfaces.py: IDatabaseWriter] :::interface
```

---

### 1.2 Thread Safety & Processing Scalability

The architecture isolates network communication from message processing by decoupling the Paho MQTT thread loop from the processing pipeline. It utilizes an internal thread-safe queue (`queue.Queue`) as a buffer.

This design allows developers to scale out processing throughput by adjusting worker thread pools (`ThreadPoolExecutor`) without blocking MQTT network connections.

#### Key Architectural Highlights:
1. **Asynchronous Decoupling**: When the Paho MQTT network thread receives incoming telemetry packets via `on_message()`, it immediately wraps them in a lightweight `RawTelemetryMessage` container and pushes them non-blockingly into an in-memory `queue.Queue`.
2. **Concurrent Worker Execution**: A background consumer loop (or pool of threads managed by `ThreadPoolExecutor`) pulls items from the buffer queue and passes each packet through the 8-stage Execution Processing Array.
3. **Thread-Safe State Management**: Stateful stages—such as `SlidingWindowDuplicateDetector` and `InMemoryDatabaseWriter`—use internal mutex locks (`threading.Lock`) to ensure zero race conditions under high-throughput concurrent load.

---

## 2. Detailed Stage Functional Specification

### Stage 1: `JsonPayloadValidator` (`validator.py`)
- **Standard Compliance**: RFC 8259 JSON, IEC 62443 Input Validation.
- **Responsibility**: Parses raw UTF-8 bytes or JSON strings into structured Python dictionaries. Enforces the presence of mandatory root fields (`message_id`, `asset_id`, `timestamp`, `readings`). Optionally validates against formal JSON Schema (`config/schema.json`).

### Stage 2: `ChronoTimestampValidator` (`timestamp_validator.py`)
- **Standard Compliance**: IEC 62443 Temporal Integrity.
- **Responsibility**: Inspects timestamp metadata against local system time. Blocks futuristic timestamp spoofing (`max_future_drift_seconds <= 5.0s`) and discards excessively stale historical packets (`max_past_drift_seconds <= 86400s`), preventing replay attacks and temporal clock drift anomalies.

### Stage 3: `SlidingWindowDuplicateDetector` (`duplicate_detector.py`)
- **Standard Compliance**: IEC 62443 Replay Attack Mitigation.
- **Responsibility**: Maintains an `OrderedDict` LRU cache of recently processed `message_id` GUIDs within a configurable sliding window (default 300 seconds). Automatically purges expired IDs and raises `DuplicatePayloadException` upon detecting duplicate submissions.

### Stage 4: `OperationalQualityChecker` (`quality_checker.py`)
- **Standard Compliance**: ISA-95 Part 2 Data Quality Codes.
- **Responsibility**: Inspects numeric sensor measurements against physical operational boundary thresholds defined in `config/validation_rules.yaml`. Assigns standardized quality status indicators (`GOOD`, `UNCERTAIN`, `BAD`).

### Stage 5: `EngineeringUnitNormalizer` (`normalizer.py`)
- **Standard Compliance**: ISA-95 Measurement Standard.
- **Responsibility**: Normalizes heterogeneous unit expressions into standardized SI / ISA-95 units (e.g., Fahrenheit/Kelvin $\rightarrow$ Celsius, PSI/kPa $\rightarrow$ bar, Hz $\rightarrow$ RPM).

### Stage 6: `StaticAssetMetadataEnricher` (`metadata_enricher.py`)
- **Standard Compliance**: ISA-95 Part 2 Asset Model.
- **Responsibility**: Resolves Level 1/2 equipment IDs against static enterprise metadata catalogs, enriching the payload with manufacturer, serial number, rated capacity, maintenance zone, and spatial hierarchy (`Enterprise -> Site -> Area -> Line -> Equipment`).

### Stage 7: `TelemetryObjectParser` (`parser.py`)
- **Standard Compliance**: Pydantic V2 Domain Object Instantiation.
- **Responsibility**: Converts intermediate dictionaries into strongly typed, validated `TelemetryPayloadModel` domain objects.

### Stage 8: `EventDispatcher` (`dispatcher.py`)
- **Standard Compliance**: Dependency Injection Storage Sink Layer.
- **Responsibility**: Delivers clean `TelemetryPayloadModel` structures to downstream database writers implementing `IDatabaseWriter` (`interfaces.py`). Supports transient failure resilience via exponential backoff (`retry_manager.py`).
