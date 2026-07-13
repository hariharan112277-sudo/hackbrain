from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from integration.backend_contracts import (
    ENTERPRISE_FAILURE_MAPPING,
    AggregationRequest,
    AlarmAcknowledgeRequest,
    ApiEnvelope,
    ContractVersion,
    EnterpriseErrorCode,
    HealthCheckResponse,
    HistoricalQueryRequest,
    HistoricalQueryResponse,
    MetricDataPoint,
    ProblemDetails,
    ProblemDetailsResponse,
    TelemetryPointResponse,
    TelemetryQuality,
    TelemetryQueryRequest,
    TelemetryStreamRequest,
    TokenObtainRequest,
    TokenResponse,
    ValidationErrorDetails,
)


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def test_telemetry_query_requires_selector_and_valid_time_window():
    now = _now()
    with pytest.raises(ValidationError):
        TelemetryQueryRequest(start_time=now, end_time=now + timedelta(minutes=5))

    request = TelemetryQueryRequest(
        start_time=now,
        end_time=now + timedelta(minutes=5),
        sensor_id=uuid4(),
        limit=5000,
    )
    assert request.sensor_id is not None
    assert request.limit == 5000


def test_telemetry_stream_requires_at_least_one_target():
    with pytest.raises(ValidationError):
        TelemetryStreamRequest()

    stream = TelemetryStreamRequest(machine_ids=[uuid4()], min_quality=TelemetryQuality.GOOD)
    assert len(stream.machine_ids) == 1


def test_alarm_acknowledge_is_contract_only_and_strict():
    ack = AlarmAcknowledgeRequest(alarm_id=uuid4(), operator_id=uuid4())
    assert ack.requested_state == "ACKNOWLEDGED"

    with pytest.raises(ValidationError):
        AlarmAcknowledgeRequest(alarm_id=uuid4(), operator_id=uuid4(), requested_state="CLEARED")


def test_aggregation_request_enforces_time_window():
    now = _now()
    req = AggregationRequest(sensor_id=uuid4(), start_time=now, end_time=now + timedelta(hours=1))
    assert "mean" in req.functions

    with pytest.raises(ValidationError):
        AggregationRequest(sensor_id=uuid4(), start_time=now, end_time=now)


def test_response_envelope_and_problem_details_are_serializable():
    now = _now()
    point = TelemetryPointResponse(
        timestamp=now,
        machine_id=uuid4(),
        sensor_id=uuid4(),
        metric_name="temperature",
        value=42.5,
        unit="C",
        quality="GOOD",
        sequence_number=1,
    )
    envelope = ApiEnvelope[TelemetryPointResponse](
        api_version=ContractVersion.V1,
        correlation_id="corr-20260713-0001",
        data=point,
    )
    assert envelope.model_dump()["data"]["metric_name"] == "temperature"

    problem = ProblemDetails(
        title="Request validation failed",
        status=422,
        detail="Invalid time range",
        correlation_id="corr-20260713-0001",
        error_code="IOB_VALIDATION_FAILED",
    )
    assert problem.retryable is False


def test_enterprise_auth_contracts_validate_email_and_token_response():
    token_request = TokenObtainRequest(
        username="operator@example.com",
        password="very-secure-password",
        client_id="iob-ui",
    )
    assert token_request.username == "operator@example.com"

    with pytest.raises(ValidationError):
        TokenObtainRequest(username="not-an-email", password="very-secure-password", client_id="iob-ui")

    token_response = TokenResponse(
        access_token="a" * 32,
        refresh_token="r" * 32,
        expires_in=3600,
    )
    assert token_response.token_type == "Bearer"


def test_historical_query_and_response_preserve_edge_and_ingest_timestamps():
    now = _now()
    query = HistoricalQueryRequest(
        machine_uuid=uuid4(),
        sensor_uuids=[uuid4()],
        start_time=now,
        end_time=now + timedelta(minutes=10),
        aggregation_resolution="1m",
    )
    assert query.pagination.limit == 50

    edge_ts = now - timedelta(seconds=2)
    point = MetricDataPoint(
        timestamp=now,
        edge_timestamp=edge_ts,
        ingest_timestamp=now,
        values={"temperature": 42.5, "running": True},
    )
    response = HistoricalQueryResponse(
        machine_uuid=query.machine_uuid,
        data_points=[point],
        total_records=1,
        execution_time_ms=8,
    )
    assert response.data_points[0].edge_timestamp == edge_ts
    assert response.data_points[0].ingest_timestamp == now


def test_health_and_problem_details_response_alias_contracts():
    health = HealthCheckResponse(
        status="HEALTHY",
        version="1.0.0",
        environment="test",
        dependencies={"database": {"status": "UP", "latency_ms": 2.5}},
    )
    assert health.dependencies["database"].status == "UP"

    detail = ValidationErrorDetails(field="machine_uuid", message="Invalid UUID", rejected_value="bad")
    problem = ProblemDetailsResponse(
        title="Request validation failed",
        status=422,
        detail="Invalid machine UUID",
        correlation_id="corr-20260713-0002",
        error_code="IOB_VALIDATION_FAILED",
        invalid_params=[detail],
    )
    assert problem.invalid_params[0].field == "machine_uuid"


def test_enterprise_failure_mapping_matrix_and_forward_compatibility():
    db_timeout = ENTERPRISE_FAILURE_MAPPING[EnterpriseErrorCode.ERR_INF_DB_01]
    assert db_timeout.http_code == 503
    assert db_timeout.detail_message_template.startswith("High-frequency telemetry")

    validation = ENTERPRISE_FAILURE_MAPPING[EnterpriseErrorCode.ERR_SYS_VAL_01]
    assert validation.http_code == 422

    response = TokenResponse(
        access_token="a" * 32,
        refresh_token="r" * 32,
        expires_in=3600,
        rolling_upgrade_field="ignored-by-contract",
    )
    assert response.extension_context == {}
    assert not hasattr(response, "rolling_upgrade_field")
