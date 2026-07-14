"""
Contract Tests
Phase 5: API schema validation and contract compliance tests.
"""

import pytest
from pydantic import ValidationError
from uuid import UUID
from datetime import datetime

from app.schemas.auth import (
    Token,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
)
from app.schemas.users import (
    UserResponse,
    UserCreate,
    UserUpdate,
    RoleResponse,
    PermissionResponse,
)
from app.schemas.industrial import (
    MachineResponse,
    MachineCreate,
    MachineUpdate,
    TelemetryResponse,
    AlarmResponse,
    AlarmSeverity,
    AlarmStatus,
    MachineStatus,
    AnomalyPredictionResponse,
    RULPredictionResponse,
)
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    MachineStatusSummary,
    TelemetryWidgetData,
    KPIWidgetData,
)


class TestAuthContracts:
    """Test authentication schema contracts."""

    def test_token_schema(self):
        """Test Token schema validation."""
        token = Token(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            expires_in=1800,
        )
        assert token.token_type == "bearer"
        assert token.expires_in == 1800

    def test_login_request_schema(self):
        """Test LoginRequest schema validation."""
        login = LoginRequest(
            email="test@example.com",
            password="SecurePass123!",
            remember_me=True,
        )
        assert login.email == "test@example.com"
        assert login.remember_me is True

    def test_login_request_invalid_email(self):
        """Test LoginRequest rejects invalid email."""
        with pytest.raises(ValidationError):
            LoginRequest(email="invalid-email", password="password")

    def test_register_request_schema(self):
        """Test RegisterRequest schema validation."""
        register = RegisterRequest(
            email="new@example.com",
            password="SecurePass123!",
            full_name="New User",
            role="operator",
        )
        assert register.email == "new@example.com"
        assert register.role == "operator"

    def test_register_request_weak_password(self):
        """Test RegisterRequest rejects weak password."""
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="weak",
                full_name="Test",
            )

    def test_register_request_password_complexity(self):
        """Test RegisterRequest enforces password complexity."""
        # Missing uppercase
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="securepass123!",
                full_name="Test",
            )
        
        # Missing lowercase
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="SECUREPASS123!",
                full_name="Test",
            )
        
        # Missing digit
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="SecurePass!",
                full_name="Test",
            )
        
        # Missing special char
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="SecurePass123",
                full_name="Test",
            )

    def test_refresh_token_request_schema(self):
        """Test RefreshTokenRequest schema validation."""
        refresh = RefreshTokenRequest(
            refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        )
        assert refresh.refresh_token.startswith("eyJ")


class TestUserContracts:
    """Test user management schema contracts."""

    def test_user_response_schema(self):
        """Test UserResponse schema validation."""
        user = UserResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            roles=["operator"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert user.email == "test@example.com"
        assert "operator" in user.roles

    def test_user_create_schema(self):
        """Test UserCreate schema validation."""
        user = UserCreate(
            email="new@example.com",
            password="SecurePass123!",
            full_name="New User",
            is_active=True,
            roles=["operator"],
        )
        assert user.email == "new@example.com"

    def test_user_update_schema(self):
        """Test UserUpdate schema validation."""
        update = UserUpdate(
            full_name="Updated Name",
            is_active=False,
        )
        assert update.full_name == "Updated Name"
        assert update.is_active is False
        assert update.email is None

    def test_role_response_schema(self):
        """Test RoleResponse schema validation."""
        role = RoleResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            name="admin",
            description="Administrator role",
            permissions=["*"],
            created_at=datetime.utcnow(),
            is_system=True,
        )
        assert role.name == "admin"
        assert role.is_system is True

    def test_permission_response_schema(self):
        """Test PermissionResponse schema validation."""
        perm = PermissionResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            name="machines:read",
            resource="machines",
            action="read",
            description="Read machines",
            created_at=datetime.utcnow(),
        )
        assert perm.resource == "machines"
        assert perm.action == "read"


class TestIndustrialContracts:
    """Test industrial IoT schema contracts."""

    def test_machine_status_enum(self):
        """Test MachineStatus enum values."""
        assert MachineStatus.ONLINE == "online"
        assert MachineStatus.OFFLINE == "offline"
        assert MachineStatus.MAINTENANCE == "maintenance"
        assert MachineStatus.ERROR == "error"
        assert MachineStatus.UNKNOWN == "unknown"

    def test_alarm_severity_enum(self):
        """Test AlarmSeverity enum values."""
        assert AlarmSeverity.CRITICAL == "critical"
        assert AlarmSeverity.HIGH == "high"
        assert AlarmSeverity.MEDIUM == "medium"
        assert AlarmSeverity.LOW == "low"
        assert AlarmSeverity.INFO == "info"

    def test_alarm_status_enum(self):
        """Test AlarmStatus enum values."""
        assert AlarmStatus.ACTIVE == "active"
        assert AlarmStatus.ACKNOWLEDGED == "acknowledged"
        assert AlarmStatus.RESOLVED == "resolved"
        assert AlarmStatus.SUPPRESSED == "suppressed"

    def test_machine_create_schema(self):
        """Test MachineCreate schema validation."""
        machine = MachineCreate(
            name="Test Machine",
            serial_number="TM-001",
            model="TM-100",
            manufacturer="Test Corp",
            location="Factory A",
            status=MachineStatus.ONLINE,
        )
        assert machine.serial_number == "TM-001"
        assert machine.status == MachineStatus.ONLINE

    def test_machine_update_schema(self):
        """Test MachineUpdate schema validation."""
        update = MachineUpdate(
            name="Updated Name",
            status=MachineStatus.MAINTENANCE,
        )
        assert update.name == "Updated Name"
        assert update.status == MachineStatus.MAINTENANCE
        assert update.serial_number is None

    def test_machine_response_schema(self):
        """Test MachineResponse schema validation."""
        machine = MachineResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            name="Test Machine",
            serial_number="TM-001",
            model="TM-100",
            manufacturer="Test Corp",
            location="Factory A",
            status=MachineStatus.ONLINE,
            tags={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert machine.name == "Test Machine"
        assert machine.status == MachineStatus.ONLINE

    def test_telemetry_response_schema(self):
        """Test TelemetryResponse schema validation."""
        telemetry = TelemetryResponse(
            machine_id=UUID("12345678-1234-5678-1234-567812345678"),
            metrics=[
                {"name": "temperature", "value": 75.5, "unit": "°C"},
            ],
            timestamp=datetime.utcnow(),
        )
        assert len(telemetry.metrics) == 1
        assert telemetry.metrics[0]["name"] == "temperature"

    def test_alarm_response_schema(self):
        """Test AlarmResponse schema validation."""
        alarm = AlarmResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            machine_id=UUID("12345678-1234-5678-1234-567812345678"),
            alarm_code="HIGH_TEMP",
            message="Temperature too high",
            severity=AlarmSeverity.HIGH,
            status=AlarmStatus.ACTIVE,
            source="sensor-1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert alarm.alarm_code == "HIGH_TEMP"
        assert alarm.severity == AlarmSeverity.HIGH
        assert alarm.status == AlarmStatus.ACTIVE

    def test_anomaly_prediction_response_schema(self):
        """Test AnomalyPredictionResponse schema validation."""
        response = AnomalyPredictionResponse(
            machine_id=UUID("12345678-1234-5678-1234-567812345678"),
            anomaly_detected=True,
            anomaly_score=0.92,
            anomaly_type="temperature_spike",
            affected_metrics=["temperature"],
            confidence=0.95,
            timestamp=datetime.utcnow(),
            model_version="v1.2.0",
        )
        assert response.anomaly_detected is True
        assert response.anomaly_score == 0.92
        assert response.confidence == 0.95

    def test_rul_prediction_response_schema(self):
        """Test RULPredictionResponse schema validation."""
        response = RULPredictionResponse(
            machine_id=UUID("12345678-1234-5678-1234-567812345678"),
            predicted_rul_hours=8760.0,
            confidence_interval={"lower": 7000.0, "upper": 10500.0},
            confidence=0.90,
            degradation_stage="normal",
            contributing_factors=["bearing_wear"],
            timestamp=datetime.utcnow(),
            model_version="v1.0.0",
        )
        assert response.predicted_rul_hours == 8760.0
        assert response.degradation_stage == "normal"


class TestDashboardContracts:
    """Test dashboard schema contracts."""

    def test_machine_status_summary_schema(self):
        """Test MachineStatusSummary schema validation."""
        summary = MachineStatusSummary(
            total=100,
            online=85,
            offline=10,
            maintenance=3,
            error=2,
            unknown=0,
        )
        assert summary.total == 100
        assert summary.online == 85

    def test_kpi_widget_data_schema(self):
        """Test KPIWidgetData schema validation."""
        kpi = KPIWidgetData(
            label="Availability",
            value=95.5,
            unit="%",
            trend=1.2,
            trend_direction="up",
            target=95.0,
            status="normal",
            timestamp=datetime.utcnow(),
        )
        assert kpi.value == 95.5
        assert kpi.trend_direction == "up"

    def test_telemetry_widget_data_schema(self):
        """Test TelemetryWidgetData schema validation."""
        widget = TelemetryWidgetData(
            machine_id=UUID("12345678-1234-5678-1234-567812345678"),
            machine_name="Test Machine",
            metric="temperature",
            unit="°C",
            current_value=75.5,
            trend=[{"timestamp": "2024-01-15T10:00:00Z", "value": 74.0}],
            threshold_warning=80.0,
            threshold_critical=90.0,
            status="normal",
            last_update=datetime.utcnow(),
        )
        assert widget.metric == "temperature"
        assert widget.status == "normal"

    def test_dashboard_overview_response_schema(self):
        """Test DashboardOverviewResponse schema validation."""
        overview = DashboardOverviewResponse(
            machine_status=MachineStatusSummary(
                total=10,
                online=8,
                offline=1,
                maintenance=1,
                error=0,
                unknown=0,
            ),
            telemetry_widgets=[],
            alarm_widget={
                "active_count": 0,
                "critical_count": 0,
                "recent_alarms": [],
                "top_machines": [],
            },
            kpi_widgets=[],
            trend_widgets=[],
            generated_at=datetime.utcnow(),
        )
        assert overview.machine_status.total == 10
        assert overview.machine_status.online == 8