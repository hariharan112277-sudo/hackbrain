# Backend Compatibility Specification

**Target Consumer:** Member 1 (Backend Systems Engineer)

This interface document guarantees that the repository abstracts built by Member 2 match the data structures, database lifecycles, and transaction requirements of Member 1's FastAPI endpoints.

## 1. Programmatic Interface Contract Matrix

| Interface Abstract Key | Input Context Types | Returned Data Entity | Null-Value Defenses |
| :--- | :--- | :--- | :--- |
| `IMachineRegistryService.get_machine` | `session: Session, machine_id: UUID` | `MachineDTO` | Raises `ResourceNotFoundError` if the asset record does not exist. |
| `ISensorRegistryService.get_sensor` | `session: Session, sensor_id: UUID` | `SensorDTO` | Fields without active readings return a standardized fallback of `None`. |
| `IHistoricalQueryService.get_historical_telemetry` | `session: Session, query: QueryCriteriaDTO` | `List[TelemetryDTO]` | Empty time windows return an empty list (`[]`) instead of throwing an error. |

## 2. Core Ingestion Constraints & Operational Caveats
* **Session Lifecycle Rules:** Member 1 must inject an open SQLAlchemy transaction context session handle into every repository call. Do not close sessions inside downstream service methods.
* **Timestamp Formatting Standards:** Every time-series field uses timezone-aware UTC objects. The repository layer normalizes incoming strings into standard Python datetime objects before processing queries.
