"""
Enterprise Application Settings utilizing Pydantic Settings v2.

This module provides centralized, type-safe configuration management across
all deployment environments (local, development, staging, production).
It extends the existing integration-layer settings with application-level
concerns such as security, logging, and CORS.
"""
import os
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Enterprise Application Settings utilizing Pydantic Settings v2."""

    # Project Identity
    PROJECT_NAME: str = Field(
        default="Enterprise Backend Core",
        description="Name of the service"
    )
    VERSION: str = Field(default="1.0.0", description="SemVer version of the application")
    API_PREFIX: str = "/api/v1"

    # Environment Strategy
    ENVIRONMENT: Literal["local", "development", "staging", "production"] = Field(
        default="local",
        description="Deployment target environment"
    )
    DEBUG: bool = Field(default=False, description="Global debug flag")

    # Security
    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_JWT_SECRET_KEY_abc123",
        description="JWT secret"
    )
    ALLOWED_HOSTS: list[str] = Field(default=["*"], description="CORS Allowed Hosts")

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Structured logger severity threshold"
    )
    JSON_LOGS: bool = Field(
        default=True,
        description="Whether to output structured JSON logs instead of human-readable text"
    )

    # --- Integration-layer settings (mirrors integration.config.IntegrationSettings) ---
    IOB_MQTT_URL: str = Field(
        default="mqtt://localhost:1883",
        description="MQTT broker URL for IOB integration layer"
    )
    IOB_TOPIC_PREFIX: str = Field(
        default="industrial/iob",
        description="MQTT topic prefix for IOB telemetry"
    )
    DEFAULT_PAGE_LIMIT: int = Field(default=100, ge=1, le=1000)
    MAX_HISTORICAL_WINDOW_DAYS: int = Field(default=30, gt=0)
    ENABLE_REALTIME_STREAMING: bool = True
    ENFORCE_OPC_QUALITY_CHECKS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def enforce_production_secrets(cls, value: str, info) -> str:
        """Prevent weak secret keys in staging/production environments."""
        env = os.getenv("ENVIRONMENT", "local")
        if env in ("staging", "production") and ("CHANGE_ME" in value or len(value) < 32):
            raise ValueError(
                f"Insecure SECRET_KEY configured for high-severity environment: '{env}'. "
                "Must be a unique cryptographically secure string of at least 32 characters."
            )
        return value


# Singleton instance — import this throughout the application
settings = AppSettings()
