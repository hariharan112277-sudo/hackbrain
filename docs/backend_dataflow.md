# System Data Flow Pipeline

The flow of industrial telemetry maps across these boundaries:

1.  **Field Ingestion:**
    Industrial Sensor -> [MQTT Topic: telemetry/{machine_id}] -> Member 2 MQTT Listener
2.  **Persistence Layer:**
    Member 2 MQTT Engine -> [Validate/Batch Write] -> Time-Series Database
3.  **Abstracted Repository:**
    Time-Series DB -> [ITelemetryRepository.get_latest_telemetry] -> IMetadataRepository
4.  **Service Orchestration:**
    IndustrialService -> [Assemble telemetry metrics, append static asset metadata] -> JSON Schema
5.  **API Client Layer:**
    FastAPI Routing Controller -> [Enforce Role Verification] -> React Dashboard (Member 4)