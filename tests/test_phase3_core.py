"""
Phase 3 Core Foundation Tests.

Validates the enterprise configuration, structured logging,
correlation middleware, exception handling, security, health probes,
and application factory.
"""
import json
import logging
import os
import sys
from io import StringIO
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Ensure the project root is importable when running from tests/
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# ===================================================================
# 1. Configuration Tests
# ===================================================================

class TestAppSettings:
    """Tests for app.core.config.AppSettings."""

    def test_default_settings_load(self):
        from app.core.config import AppSettings
        settings = AppSettings()
        assert settings.PROJECT_NAME == "Enterprise Backend Core"
        assert settings.VERSION == "1.0.0"
        assert settings.API_PREFIX == "/api/v1"
        assert settings.ENVIRONMENT == "local"
        assert settings.DEBUG is False
        assert settings.LOG_LEVEL == "INFO"
        assert settings.JSON_LOGS is True

    def test_settings_from_env_vars(self, monkeypatch):
        from app.core.config import AppSettings
        monkeypatch.setenv("PROJECT_NAME", "Test Service")
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("JSON_LOGS", "false")

        settings = AppSettings()
        assert settings.PROJECT_NAME == "Test Service"
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is True
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.JSON_LOGS is False

    def test_secret_key_validator_blocks_weak_in_prod(self, monkeypatch):
        from app.core.config import AppSettings
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "CHANGE_ME_short")

        with pytest.raises(Exception):
            AppSettings()

    def test_secret_key_validator_allows_strong_in_prod(self, monkeypatch):
        from app.core.config import AppSettings
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "a" * 32 + "_strong_secret_key_here_1234567890")

        settings = AppSettings()
        assert len(settings.SECRET_KEY) >= 32

    def test_integration_settings_mirrored(self):
        from app.core.config import settings
        assert hasattr(settings, "IOB_MQTT_URL")
        assert hasattr(settings, "IOB_TOPIC_PREFIX")
        assert hasattr(settings, "DEFAULT_PAGE_LIMIT")
        assert hasattr(settings, "ENABLE_REALTIME_STREAMING")


# ===================================================================
# 2. Structured Logging Tests
# ===================================================================

class TestStructuredLogging:
    """Tests for app.core.logging_config module."""

    def test_json_formatter_outputs_valid_json(self):
        from app.core.logging_config import StructuredJSONFormatter, correlation_id_ctx

        formatter = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.msecs = 123.0

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["logger"] == "test.logger"
        assert parsed["module"] == "test"
        assert "timestamp" in parsed
        assert "correlation_id" in parsed

    def test_json_formatter_includes_extra_fields(self):
        from app.core.logging_config import StructuredJSONFormatter

        formatter = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.msecs = 0.0
        record.extra_fields = {"custom_key": "custom_value", "count": 42}

        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["custom_key"] == "custom_value"
        assert parsed["count"] == 42

    def test_json_formatter_includes_exception_info(self):
        from app.core.logging_config import StructuredJSONFormatter

        formatter = StructuredJSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys as _sys
            exc_info = _sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        record.msecs = 0.0

        output = formatter.format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_setup_structured_logging_configures_root_logger(self):
        from app.core.logging_config import setup_structured_logging

        # Reset root logger
        root = logging.getLogger()
        for h in root.handlers[:]:
            root.removeHandler(h)

        setup_structured_logging("DEBUG", json_format=True)

        assert root.level == logging.DEBUG
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.StreamHandler)

        # Cleanup
        for h in root.handlers[:]:
            root.removeHandler(h)

    def test_correlation_id_context_var(self):
        from app.core.logging_config import correlation_id_ctx

        # Default should be empty string
        assert correlation_id_ctx.get() == ""

        # Set and retrieve
        token = correlation_id_ctx.set("test-corr-123")
        assert correlation_id_ctx.get() == "test-corr-123"

        # Reset
        correlation_id_ctx.reset(token)
        assert correlation_id_ctx.get() == ""


# ===================================================================
# 3. Middleware Tests
# ===================================================================

class TestCorrelationMiddleware:
    """Tests for CorrelationAndLoggingMiddleware."""

    def _create_test_app(self):
        from app.core.logging_config import CorrelationAndLoggingMiddleware

        test_app = FastAPI()
        test_app.add_middleware(CorrelationAndLoggingMiddleware)

        @test_app.get("/test")
        def test_endpoint():
            return {"status": "ok"}

        @test_app.get("/error")
        def error_endpoint():
            raise RuntimeError("test error")

        return test_app

    def test_correlation_id_generated_when_not_provided(self):
        client = TestClient(self._create_test_app(), raise_server_exceptions=False)
        response = client.get("/test")
        assert response.status_code == 200
        assert "x-correlation-id" in response.headers
        assert len(response.headers["x-correlation-id"]) > 0

    def test_correlation_id_preserved_from_header(self):
        client = TestClient(self._create_test_app(), raise_server_exceptions=False)
        custom_id = "my-custom-correlation-id-12345"
        response = client.get("/test", headers={"X-Correlation-ID": custom_id})
        assert response.status_code == 200
        assert response.headers["x-correlation-id"] == custom_id

    def test_correlation_id_returned_on_error(self):
        client = TestClient(self._create_test_app(), raise_server_exceptions=False)
        response = client.get("/error")
        assert response.status_code == 500
        assert "x-correlation-id" in response.headers


# ===================================================================
# 4. Exception Handler Tests
# ===================================================================

class TestExceptionHandlers:
    """Tests for app.core.exceptions module."""

    def _create_test_app_with_handlers(self):
        from app.core.exceptions import register_exception_handlers

        test_app = FastAPI()
        register_exception_handlers(test_app)
        return test_app

    def test_app_base_exception_handler(self):
        from app.core.exceptions import AppBaseException

        test_app = self._create_test_app_with_handlers()

        @test_app.get("/app-error")
        def app_error():
            raise AppBaseException("Something went wrong", status_code=400)

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/app-error")
        assert response.status_code == 400

        body = response.json()
        assert body["success"] is False
        assert body["error"] == "AppBaseException"
        assert body["message"] == "Something went wrong"
        assert body["details"] == {}

    def test_authentication_error_handler(self):
        from app.core.exceptions import AuthenticationError

        test_app = self._create_test_app_with_handlers()

        @test_app.get("/auth-error")
        def auth_error():
            raise AuthenticationError()

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/auth-error")
        assert response.status_code == 401

        body = response.json()
        assert body["success"] is False
        assert body["error"] == "AuthenticationError"
        assert "Invalid credentials" in body["message"]

    def test_resource_not_found_error_handler(self):
        from app.core.exceptions import ResourceNotFoundError

        test_app = self._create_test_app_with_handlers()

        @test_app.get("/not-found")
        def not_found():
            raise ResourceNotFoundError("Machine", "abc-123")

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/not-found")
        assert response.status_code == 404

        body = response.json()
        assert body["success"] is False
        assert body["error"] == "ResourceNotFoundError"
        assert "Machine" in body["message"]
        assert "abc-123" in body["message"]

    def test_iob_integration_exception_handler(self):
        from integration.exceptions import ResourceNotFoundError

        test_app = self._create_test_app_with_handlers()

        @test_app.get("/iob-not-found")
        def iob_not_found():
            raise ResourceNotFoundError(
                "Machine not found",
                details={"machine_id": "abc-123"}
            )

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/iob-not-found")
        assert response.status_code == 404

        body = response.json()
        assert body["success"] is False
        assert body["error"] == "ResourceNotFoundError"
        assert body["message"] == "Machine not found"
        assert body["details"]["machine_id"] == "abc-123"

    def test_iob_mqtt_transport_exception_returns_503(self):
        from integration.exceptions import MQTTTransportException

        test_app = self._create_test_app_with_handlers()

        @test_app.get("/mqtt-error")
        def mqtt_error():
            raise MQTTTransportException("Broker unreachable")

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/mqtt-error")
        assert response.status_code == 503

        body = response.json()
        assert body["success"] is False
        assert body["error"] == "MQTTTransportException"

    def test_iob_database_unavailable_exception_returns_503(self):
        from integration.exceptions import DatabaseUnavailableException

        test_app = self._create_test_app_with_handlers()

        @test_app.get("/db-error")
        def db_error():
            raise DatabaseUnavailableException("Connection timeout")

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/db-error")
        assert response.status_code == 503

        body = response.json()
        assert body["success"] is False
        assert body["error"] == "DatabaseUnavailableException"

    def test_validation_exception_handler(self):
        from pydantic import BaseModel

        test_app = self._create_test_app_with_handlers()

        class Item(BaseModel):
            name: str
            quantity: int

        @test_app.post("/items")
        def create_item(item: Item):
            return item

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.post("/items", json={"name": "test"})  # missing quantity
        assert response.status_code == 422

        body = response.json()
        assert body["success"] is False
        assert body["error"] == "ValidationError"
        assert "details" in body
        assert len(body["details"]) > 0
        assert body["details"][0]["field"] == "body -> quantity"

    def test_starlette_http_exception_handler(self):
        from fastapi import HTTPException

        test_app = self._create_test_app_with_handlers()

        @test_app.get("/http-error")
        def http_error():
            raise HTTPException(status_code=403, detail="Forbidden")

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/http-error")
        assert response.status_code == 403

        body = response.json()
        assert body["success"] is False
        assert body["error"] == "HTTPException"
        assert body["message"] == "Forbidden"

    def test_unhandled_exception_handler(self):
        test_app = self._create_test_app_with_handlers()

        @test_app.get("/crash")
        def crash():
            raise RuntimeError("unexpected failure")

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/crash")
        assert response.status_code == 500

        body = response.json()
        assert body["success"] is False
        assert body["error"] == "InternalServerError"
        # Should NOT leak internal details
        assert "unexpected failure" not in body["message"]


# ===================================================================
# 5. Integration Logger Tests
# ===================================================================

class TestIntegrationLogger:
    """Tests for integration.logger backward compatibility."""

    def test_get_integration_logger_returns_logger(self):
        from integration.logger import get_integration_logger
        logger = get_integration_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "iob.integration"

    def test_get_integration_logger_custom_name(self):
        from integration.logger import get_integration_logger
        logger = get_integration_logger("custom.module")
        assert logger.name == "custom.module"


# ===================================================================
# 6. Application Factory Tests
# ===================================================================

class TestApplicationFactory:
    """Tests for app.main.create_app() factory."""

    def test_create_app_returns_fastapi_instance(self):
        from app.main import create_app
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_health_endpoint(self):
        from app.main import create_app
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_api_info_endpoint(self):
        from app.main import create_app
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "features" in data

    def test_correlation_id_in_response(self):
        from app.main import create_app
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert "x-correlation-id" in response.headers

    def test_custom_correlation_id_preserved(self):
        from app.main import create_app
        app = create_app()
        client = TestClient(app)
        custom_id = "test-correlation-abc-123"
        response = client.get("/health", headers={"X-Correlation-ID": custom_id})
        assert response.headers["x-correlation-id"] == custom_id

    def test_cors_middleware_configured(self):
        from app.main import create_app
        app = create_app()
        # Check that CORS middleware is in the stack
        cors_found = False
        for middleware in app.user_middleware:
            if "cors" in str(middleware.klass).lower():
                cors_found = True
                break
        assert cors_found


# ===================================================================
# 7. Full Application Integration Test
# ===================================================================

class TestFullApplication:
    """End-to-end test of the wired FastAPI application via root main.py."""

    def test_health_endpoint(self):
        from main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self):
        from main import app
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"

    def test_api_status_endpoint(self):
        from main import app
        client = TestClient(app)
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_correlation_id_in_response(self):
        from main import app
        client = TestClient(app)
        response = client.get("/health")
        assert "x-correlation-id" in response.headers

    def test_custom_correlation_id_preserved(self):
        from main import app
        client = TestClient(app)
        custom_id = "test-correlation-abc-123"
        response = client.get("/health", headers={"X-Correlation-ID": custom_id})
        assert response.headers["x-correlation-id"] == custom_id

    def test_exception_handlers_registered(self):
        from main import app
        client = TestClient(app, raise_server_exceptions=False)
        # Trigger an unhandled exception
        @app.get("/test-crash")
        def crash():
            raise RuntimeError("test")

        response = client.get("/test-crash")
        assert response.status_code == 500
        body = response.json()
        assert body["success"] is False
        assert body["error"] == "InternalServerError"


# ===================================================================
# 8. Security Headers Tests
# ===================================================================

class TestSecurityHeaders:
    """Tests for app.core.security module."""

    def test_security_headers_injected(self):
        from app.core.security import SecurityHeadersMiddleware

        test_app = FastAPI()
        test_app.add_middleware(SecurityHeadersMiddleware)

        @test_app.get("/test")
        def test_endpoint():
            return {"status": "ok"}

        client = TestClient(test_app)
        response = client.get("/test")
        assert response.status_code == 200
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")
        assert "max-age=31536000" in response.headers.get("Strict-Transport-Security", "")
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_password_hashing(self):
        from app.core.security import hash_password, verify_password

        password = "SecureP@ssw0rd!"
        hashed = hash_password(password)

        # Hashed password should be different from plain text
        assert hashed != password
        # Should verify correctly
        assert verify_password(password, hashed) is True
        # Wrong password should fail
        assert verify_password("wrong_password", hashed) is False

    def test_jwt_create_and_decode(self):
        from app.core.security import create_access_token, decode_access_token
        from datetime import timedelta

        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data, expires_delta=timedelta(minutes=30))

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"
        assert "exp" in decoded

    def test_jwt_expired_token_returns_none(self):
        from app.core.security import create_access_token, decode_access_token
        from datetime import timedelta

        data = {"sub": "user123"}
        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        decoded = decode_access_token(token)
        assert decoded is None

    def test_jwt_invalid_token_returns_none(self):
        from app.core.security import decode_access_token

        decoded = decode_access_token("invalid.token.here")
        assert decoded is None

    def test_security_headers_middleware_in_factory_app(self):
        from app.main import create_app
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Frame-Options" in response.headers
        assert "Strict-Transport-Security" in response.headers


# ===================================================================
# 9. Health Probe Tests
# ===================================================================

class TestHealthProbes:
    """Tests for app.core.health module."""

    def test_liveness_probe(self):
        from app.main import create_app
        app = create_app()
        client = TestClient(app)
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_readiness_probe_healthy(self):
        from app.main import create_app
        app = create_app()
        client = TestClient(app)
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "healthy"

    def test_readiness_probe_unhealthy(self):
        from app.main import create_app
        from app.core.health import check_database_connection
        from unittest.mock import patch

        app = create_app()

        # Mock database check to return False
        with patch("app.core.health.check_database_connection", return_value=False):
            client = TestClient(app)
            response = client.get("/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unready"
            assert data["checks"]["database"] == "unhealthy"

    def test_health_router_in_factory(self):
        from app.main import create_app
        app = create_app()

        # Verify health routes are registered
        routes = [route.path for route in app.routes]
        assert "/health/live" in routes
        assert "/health/ready" in routes

    def test_legacy_health_endpoint_still_works(self):
        from app.main import create_app
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
