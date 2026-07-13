# Enterprise Response Schema Specifications (response_models.md)

Executable source of truth: `integration/backend_contracts.py`.

## 1. Authentication Domain Structure

```python
class TokenResponse(ContractBaseModel):
    access_token: str = Field(..., description="Cryptographically signed JSON Web Token")
    refresh_token: str = Field(..., description="High-entropy opaque lifecycle extension token string")
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int = Field(..., description="Relative token execution duration remaining in seconds")
```

## 2. Machine Metadata Digital Twin Structure

```python
class MachineResponse(ContractBaseModel):
    uuid: UUID = Field(..., description="Global Unique Asset Identifier")
    display_name: str = Field(..., min_length=1, max_length=255)
    model_number: str
    manufacturer: str
    installation_date: str
    operational_status: Literal["ONLINE", "OFFLINE", "MAINTENANCE", "FAULTED"]
    telemetry_metadata: dict[str, Any] = Field(..., description="Dynamic hardware properties structural configuration")
```

## 3. Time-Series Metrics Payload Structure

```python
class MetricDataPoint(ContractBaseModel):
    timestamp: datetime
    edge_timestamp: datetime | None
    ingest_timestamp: datetime | None
    values: dict[str, float | int | str | bool]

class HistoricalQueryResponse(ContractBaseModel):
    machine_uuid: UUID
    data_points: list[MetricDataPoint]
    total_records: int
    execution_time_ms: int
```

Timestamp drift mitigation is contractually represented by preserving both `edge_timestamp` and `ingest_timestamp` where a telemetry source provides them.

## 4. Core System Infrastructure Diagnostics

```python
class SubsystemStatus(ContractBaseModel):
    status: Literal["UP", "DOWN", "DEGRADED"]
    latency_ms: float

class HealthCheckResponse(ContractBaseModel):
    status: Literal["HEALTHY", "UNHEALTHY"]
    version: str
    environment: str
    dependencies: dict[str, SubsystemStatus]
```

## 5. Compatibility Response Envelope

```python
class ApiEnvelope[T](ContractBaseModel):
    api_version: ContractVersion
    correlation_id: str
    data: T
    errors: list[ProblemDetails]
```
