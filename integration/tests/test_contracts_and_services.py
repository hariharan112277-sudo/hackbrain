"""
Integration Layer Contract Verification Test Suite.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from integration.contracts import TelemetryDTO, QueryCriteriaDTO
from integration.exceptions import InvalidQueryCriteriaException
from integration.query_service import HistoricalQueryService
from integration.examples.backend_orchestration_sample import ConcreteTelemetryRepoMock


def test_telemetry_dto_industrial_quality_bounds():
    """Validates structural constraints and OPC standard code enforcement rules within Pydantic DTOs."""
    valid_id = uuid4()
    m_id = uuid4()
    s_id = uuid4()

    # Verify model constraints accept official OPC input codes
    dto = TelemetryDTO(
        id=valid_id, timestamp=datetime.now(timezone.utc), machine_id=m_id, sensor_id=s_id,
        measured_value=142.84, quality_code=192, sequence_number=12001
    )
    assert dto.quality_code == 192

    # Verify validation errors are thrown on unauthorized, out-of-bounds standard code inputs
    with pytest.raises(ValidationError):
        TelemetryDTO(
            id=valid_id, timestamp=datetime.now(timezone.utc), machine_id=m_id, sensor_id=s_id,
            measured_value=142.84, quality_code=255, sequence_number=12001  # 255 is invalid
        )


def test_historical_query_chronological_inversion_guard():
    """Ensures that chronological errors inside query configurations trigger custom integration exceptions."""
    telemetry_repo_mock = ConcreteTelemetryRepoMock()
    query_service = HistoricalQueryService(
        telemetry_repo=telemetry_repo_mock, alarm_repo=None, event_repo=None, maintenance_repo=None
    )

    invalid_criteria = QueryCriteriaDTO(
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) - timedelta(hours=6),  # Inverted boundary parameters
        page=1, limit=100
    )

    with pytest.raises(InvalidQueryCriteriaException):
        query_service.get_historical_telemetry("MockSession", uuid4(), invalid_criteria)
