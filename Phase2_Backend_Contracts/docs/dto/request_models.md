# Enterprise Request Schema Specifications (request_models.md)

All structures use explicit strict typing rules through standard data modeling constraints. Source of truth for executable schemas: `integration/backend_contracts.py`.

## 1. Authentication Domain Contracts

```python
class TokenObtainRequest(ContractBaseModel):
    username: EmailIdentity = Field(..., description="Valid corporate email format identity")
    password: str = Field(..., min_length=12, max_length=128, description="Secured plaintext credential string")
    client_id: str = Field(..., min_length=3, max_length=64)

class TokenRevokeRequest(ContractBaseModel):
    refresh_token: str = Field(..., min_length=32, max_length=4096)
    client_id: str = Field(..., min_length=3, max_length=64)
```

Implementation note: The documentation-level contract uses the `EmailStr` concept. The executable schema uses a strict email regex alias (`EmailIdentity`) to avoid introducing an undeclared optional `email-validator` runtime dependency into the current repository.

## 2. Infrastructure & Query Pagination Contracts

```python
class PaginationParams(ContractBaseModel):
    page: int = Field(default=1, ge=1, description="Target page window index")
    limit: int = Field(default=50, ge=1, le=1000, description="Enforced item retrieval limit per window frame")
```

## 3. Industrial Telemetry & Historical Query Domain Contracts

```python
class HistoricalQueryRequest(TimeWindowRequest):
    machine_uuid: UUID
    sensor_uuids: list[UUID] = Field(..., min_length=1, max_length=100)
    start_time: datetime = Field(..., description="ISO 8601 start interval boundary")
    end_time: datetime = Field(..., description="ISO 8601 end interval boundary")
    aggregation_resolution: Literal["1s", "10s", "1m", "5m", "1h"] = "1m"
    pagination: PaginationParams = Field(default_factory=PaginationParams)
```

Validation:
- `end_time` must be greater than `start_time`.
- `sensor_uuids` must contain 1 to 100 UUID values.
- `machine_uuid` is a UUID object at the Python boundary and a UUID string in JSON.

## 4. Alarm Filtering Domain Contracts

```python
class AlarmFilterRequest(ContractBaseModel):
    severity: Literal["INFO", "WARNING", "CRITICAL", "FATAL"] | None = None
    is_acknowledged: bool | None = None
    start_time: datetime | None = None
    pagination: PaginationParams = Field(default_factory=PaginationParams)
```

## 5. Existing Telemetry Query Compatibility Contract

```python
class TelemetryQueryRequest(TimeWindowRequest):
    machine_id: UUID | None = None
    sensor_id: UUID | None = None
    metric_names: list[str] = Field(default_factory=list, max_length=64)
    quality_filter: list[TelemetryQuality] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=100, ge=1, le=5000)
    sort_direction: SortDirection = SortDirection.ASC
```

This model remains available for the `/api/v1/iob/telemetry/query` design path while `HistoricalQueryRequest` covers the enterprise `/api/v1/historical/query` path.
