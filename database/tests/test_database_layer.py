"""
Infrastructure verification scripts validating structural performance boundaries,
transaction isolation properties, and repository abstraction integrity.
"""

import pytest
from datetime import datetime, timezone
import uuid

from database.connection import connection_manager, DatabaseConnectionManager
from database.repository import AssetRepository, TelemetryRepository
from database.models import (
    Base, Asset, OperationalStatus, Plant, ProductionLine,
    Gateway, Machine, Sensor, Operator
)
from database.exceptions import ConstraintViolationError, RecordNotFoundError


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """Initializes in-memory test database schema and seeds master verification rows."""
    # Ensure connection manager uses sqlite memory for sandboxed unit tests if not live postgres
    db_mgr = DatabaseConnectionManager(db_url="sqlite:///:memory:")
    Base.metadata.create_all(db_mgr.engine)

    session = db_mgr.get_session()
    try:
        # Seed master verification rows required by tests
        plant = Plant(
            id=uuid.UUID('e00bbdf8-2b28-48b8-b80c-03d3c14c514d'),
            name="Stuttgart Assembly Complex Hub-4",
            location="Stuttgart, Germany"
        )
        line = ProductionLine(
            id=uuid.UUID('a7a3bfa4-61c1-4b13-899a-cbbf628b0821'),
            plant_id=plant.id,
            name="Main Powertrain Cell Line A",
            sequence_number=1
        )
        gw = Gateway(
            id=uuid.UUID('c53b2160-b996-48c6-829d-ee18d7f45778'),
            name="GW-EDGE-01",
            ip_address="10.142.41.5",
            mac_address="00:1A:2B:3C:4D:5E",
            firmware_version="v4.2.1-build82",
            protocol="MQTT",
            status=OperationalStatus.ONLINE
        )
        asset = Asset(
            id=uuid.UUID('f65efea9-a1b1-4f11-92be-154a4f89d311'),
            production_line_id=line.id,
            name="KUKA Titan Heavy Load Robotic Arm",
            category="Robotics",
            manufacturer="KUKA AG",
            model="KR-1000-TITAN",
            serial_number="SN-KUKA-992182",
            criticality="Mission-Critical",
            installation_date=datetime.now(timezone.utc),
            status=OperationalStatus.ONLINE
        )
        machine = Machine(
            id=uuid.UUID('182bcfb2-4d1a-4da2-9b24-9dfc120fb211'),
            asset_id=asset.id,
            gateway_id=gw.id,
            firmware_version="firmware-kuka-v9.1",
            operating_hours=1240.5,
            runtime_counter=340.2,
            current_mode="AUTOMATIC"
        )
        sensor1 = Sensor(
            id=uuid.UUID('bd5bcefa-9fa1-4191-88bc-41829daff911'),
            machine_id=machine.id,
            name="Axis-3 Vibration Node",
            sensor_type="Vibration",
            measurement_unit="mm/s",
            sampling_rate_hz=1000.0,
            status=OperationalStatus.ONLINE
        )
        sensor2 = Sensor(
            id=uuid.UUID('293bcffa-1ab2-41f2-99ca-2182bba11411'),
            machine_id=machine.id,
            name="Primary Windings Temp Thermal Couple",
            sensor_type="Temperature",
            measurement_unit="Celsius",
            sampling_rate_hz=10.0,
            status=OperationalStatus.ONLINE
        )
        operator = Operator(
            id=uuid.UUID('518bcffa-99ab-4411-bc29-4182baaa9115'),
            badge_number="BADGE-8821",
            first_name="Dieter",
            last_name="Eisler",
            assigned_shift="DAY",
            is_active=True
        )

        session.add_all([plant, line, gw, asset, machine, sensor1, sensor2, operator])
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()

    yield
    db_mgr.shutdown()


@pytest.fixture(scope="function")
def db_session():
    """Provides a transactional database session for tests."""
    session = connection_manager.get_session()
    yield session
    session.rollback()
    session.close()


def test_connection_health():
    """Validates basic database connectivity and health checking."""
    assert connection_manager.check_health() is True


def test_asset_creation_and_lookup(db_session):
    """Verifies complete lifecycles for structured master asset records."""
    repo = AssetRepository()
    asset_id = uuid.uuid4()

    new_asset = Asset(
        id=asset_id,
        production_line_id=uuid.UUID('a7a3bfa4-61c1-4b13-899a-cbbf628b0821'),  # seeded row id
        name="Axis Test Hydraulic Unit",
        category="Hydraulics",
        manufacturer="Bosch Rexroth",
        model="Rex-H-100",
        serial_number=f"SN-TEST-{uuid.uuid4().hex[:6]}",
        criticality="High",
        installation_date=datetime.now(timezone.utc),
        status=OperationalStatus.ONLINE
    )

    saved = repo.save(db_session, new_asset)
    assert saved.id == asset_id

    fetched = repo.find_by_id(db_session, asset_id)
    assert fetched.name == "Axis Test Hydraulic Unit"


def test_unique_constraint_violation(db_session):
    """Ensures database constraint exceptions are caught and correctly mapped."""
    repo = AssetRepository()
    shared_serial = f"SN-DUPLICATE-{uuid.uuid4().hex[:6]}"

    asset_a = Asset(
        id=uuid.uuid4(),
        production_line_id=uuid.UUID('a7a3bfa4-61c1-4b13-899a-cbbf628b0821'),
        name="Asset Alpha", category="Electrical", manufacturer="ABB", model="M1",
        serial_number=shared_serial, criticality="Low", installation_date=datetime.now(timezone.utc)
    )
    repo.save(db_session, asset_a)

    asset_b = Asset(
        id=uuid.uuid4(),
        production_line_id=uuid.UUID('a7a3bfa4-61c1-4b13-899a-cbbf628b0821'),
        name="Asset Beta", category="Electrical", manufacturer="ABB", model="M2",
        serial_number=shared_serial, criticality="Low", installation_date=datetime.now(timezone.utc)
    )

    with pytest.raises(ConstraintViolationError):
        repo.save(db_session, asset_b)


def test_bulk_telemetry_performance(db_session):
    """Validates the high-throughput bulk ingestion path."""
    repo = TelemetryRepository()
    machine_id = uuid.UUID('182bcfb2-4d1a-4da2-9b24-9dfc120fb211')
    sensor_id = uuid.UUID('bd5bcefa-9fa1-4191-88bc-41829daff911')

    payload_batch = [
        {
            "id": uuid.uuid4(),
            "timestamp": datetime.now(timezone.utc),
            "machine_id": machine_id,
            "sensor_id": sensor_id,
            "measured_value": 4.12 + i,
            "quality_code": 192,
            "alarm_status": "NORMAL",
            "sequence_number": 1000 + i,
            "metadata_fields": {}
        }
        for i in range(500)
    ]

    inserted_count = repo.bulk_insert_telemetry(db_session, payload_batch)
    assert inserted_count == 500
