import uuid
from datetime import datetime, timezone, timedelta
import pytest
from pydantic import ValidationError

from integration.contracts import (
    TelemetryDTO, QueryCriteriaDTO, OperationalStatus
)
from integration.exceptions import ResourceNotFoundError, InvalidQueryCriteriaException
from integration.services import (
    MachineRegistryService,
    SensorRegistryService,
    HistoricalQueryService,
    MQTTIntegrationService,
    TelemetryIntegrationService,
    AssetIntegrationService,
    MetadataIntegrationService
)
from database.connection import DatabaseConnectionManager
from database.models import Base, Asset, Machine, Sensor, Telemetry, Plant, ProductionLine, Gateway


@pytest.fixture(scope="module")
def integration_db():
    db_mgr = DatabaseConnectionManager(db_url="sqlite:///:memory:")
    Base.metadata.create_all(db_mgr.engine)
    session = db_mgr.get_session()
    try:
        plant = Plant(id=uuid.uuid4(), name="Int-Plant", location="Munich")
        line = ProductionLine(id=uuid.uuid4(), plant_id=plant.id, name="Int-Line", sequence_number=1)
        gw = Gateway(id=uuid.uuid4(), name="Int-GW", ip_address="10.0.0.1", mac_address="AA:BB:CC:DD:EE:FF", firmware_version="v1")
        asset = Asset(
            id=uuid.uuid4(), production_line_id=line.id, name="Int-Asset", category="Robotics",
            manufacturer="ABB", model="IRB", serial_number="SN-INT-01", criticality="High",
            installation_date=datetime.now(timezone.utc)
        )
        machine = Machine(id=uuid.uuid4(), asset_id=asset.id, gateway_id=gw.id, firmware_version="v2", operating_hours=50.0)
        sensor = Sensor(id=uuid.uuid4(), machine_id=machine.id, name="Int-Sensor", sensor_type="Vibration", measurement_unit="mm/s", sampling_rate_hz=100.0)
        telemetry = Telemetry(
            id=uuid.uuid4(), timestamp=datetime.now(timezone.utc), machine_id=machine.id,
            sensor_id=sensor.id, measured_value=15.2, quality_code=192, sequence_number=1
        )
        session.add_all([plant, line, gw, asset, machine, sensor, telemetry])
        session.commit()
    finally:
        session.close()

    yield db_mgr
    db_mgr.shutdown()


def test_telemetry_dto_opc_quality_validation():
    # Valid OPC code
    dto = TelemetryDTO(
        id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        machine_id=uuid.uuid4(),
        sensor_id=uuid.uuid4(),
        measured_value=10.0,
        quality_code=192,
        sequence_number=1
    )
    assert dto.quality_code == 192

    # Invalid OPC code
    with pytest.raises(ValidationError) as exc:
        TelemetryDTO(
            id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            machine_id=uuid.uuid4(),
            sensor_id=uuid.uuid4(),
            measured_value=10.0,
            quality_code=99,
            sequence_number=1
        )
    assert "Invalid industrial OPC quality" in str(exc.value)


def test_machine_registry_service(integration_db):
    session = integration_db.get_session()
    try:
        service = MachineRegistryService()
        machines = service.list_machines(session)
        assert len(machines) >= 1
        m_id = machines[0].id
        dto = service.get_machine(session, m_id)
        assert dto.operating_hours == 50.0
        assert service.lookup_status(session, m_id) == OperationalStatus.ONLINE
    finally:
        session.close()


def test_sensor_registry_service(integration_db):
    session = integration_db.get_session()
    try:
        service = SensorRegistryService()
        m_service = MachineRegistryService()
        m_id = m_service.list_machines(session)[0].id
        sensors = service.list_sensors_by_machine(session, m_id)
        assert len(sensors) >= 1
        s_id = sensors[0].id
        cal_dto = service.execute_calibration(session, s_id, calibration_offset=0.5)
        assert cal_dto.calibration_offset == 0.5
    finally:
        session.close()


def test_historical_query_service(integration_db):
    session = integration_db.get_session()
    try:
        s_service = SensorRegistryService()
        m_service = MachineRegistryService()
        m_id = m_service.list_machines(session)[0].id
        s_id = s_service.list_sensors_by_machine(session, m_id)[0].id

        h_service = HistoricalQueryService()
        now = datetime.now(timezone.utc)
        criteria = QueryCriteriaDTO(
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=1),
            page=1, limit=10
        )
        t_dtos = h_service.get_historical_telemetry(session, s_id, criteria)
        assert len(t_dtos) >= 1

        stats = h_service.get_aggregated_statistics(session, s_id, now - timedelta(days=1), now + timedelta(days=1))
        assert stats.datapoint_count >= 1
        assert stats.mean_value == 15.2

        # Test invalid criteria exception
        bad_criteria = QueryCriteriaDTO(
            start_time=now + timedelta(days=1),
            end_time=now - timedelta(days=1)
        )
        with pytest.raises(InvalidQueryCriteriaException):
            h_service.get_historical_telemetry(session, s_id, bad_criteria)
    finally:
        session.close()


def test_mqtt_and_metadata_services():
    mqtt_svc = MQTTIntegrationService()
    status = mqtt_svc.get_broker_status()
    assert status["status"] == "CONNECTED"
    m_id = uuid.uuid4()
    assert "telemetry" in mqtt_svc.resolve_machine_topic(m_id)

    meta_svc = MetadataIntegrationService()
    units = meta_svc.get_engineering_units_map()
    assert units["TEMPERATURE"] == "CELSIUS"
