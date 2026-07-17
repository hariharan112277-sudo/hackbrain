"""Central application configuration and production safety boundaries."""

from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEVELOPMENT_SECRET = "development-only-secret-key-change-before-deploying"
_DEVELOPMENT_DATABASE_URL = "sqlite:///./iob_development.db"


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Development has usable local defaults. Production deliberately fails during
    settings construction when required secrets or connection details are
    absent, blank, or still set to a development fallback.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        validate_default=True,
    )

    # Application identity and deployment context
    APP_NAME: str = "Industrial Operating Brain"
    APP_VERSION: str = "5.0.0"
    PROJECT_NAME: str = "Enterprise Backend Core"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    ENV: str = Field(
        default="development",
        description="Deployment context used by repository runtime gates",
    )
    ENVIRONMENT: str = Field(
        default="local",
        description="Compatibility deployment context used by the core platform",
    )
    USE_STUB_REPOSITORIES: bool = Field(
        default=True,
        description="Selects volatile repositories instead of persistent adapters",
    )
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = Field(default=_DEVELOPMENT_SECRET, description="Secret key for JWT signing")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 12
    BCRYPT_ROUNDS: int = 12

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )
    ALLOWED_HOSTS: List[str] = Field(default_factory=lambda: ["*"])

    # Database
    DATABASE_URL: Optional[str] = Field(
        default=_DEVELOPMENT_DATABASE_URL,
        description="SQLAlchemy database connection string",
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5

    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_CLIENT_ID: str = "iob-backend"
    MQTT_KEEPALIVE: int = 60
    MQTT_TLS_ENABLED: bool = False
    IOB_MQTT_URL: str = "mqtt://localhost:1883"
    IOB_TOPIC_PREFIX: str = "industrial/iob"

    # Integration limits and feature switches
    DEFAULT_PAGE_LIMIT: int = 100
    MAX_HISTORICAL_WINDOW_DAYS: int = 30
    ENABLE_REALTIME_STREAMING: bool = True
    ENFORCE_OPC_QUALITY_CHECKS: bool = True

    # AI and frontend services
    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_TIMEOUT: int = 30
    AI_ANOMALY_ENDPOINT: str = "/predict/anomaly"
    AI_RUL_ENDPOINT: str = "/predict/rul"
    AI_HEALTH_ENDPOINT: str = "/health"
    FRONTEND_URL: str = "http://localhost:3000"

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    JSON_LOGS: bool = True

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    # Feature flags
    ENABLE_AI_INTEGRATION: bool = True
    ENABLE_REALTIME_TELEMETRY: bool = True
    ENABLE_ALARM_NOTIFICATIONS: bool = True

    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_string_list(cls, value: str | List[str]) -> List[str]:
        """Accept either JSON-style lists or comma-separated environment values."""
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                import json

                parsed = json.loads(stripped)
                if not isinstance(parsed, list):
                    raise ValueError("Expected a list")
                return [str(item).strip() for item in parsed]
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("ENV", "ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return str(value).strip().lower()

    @model_validator(mode="after")
    def validate_production_boundaries(self) -> "Settings":
        """Reject missing or development-grade production configuration."""
        if not self.is_production:
            return self

        if len(self.SECRET_KEY.strip()) < 32 or self.SECRET_KEY == _DEVELOPMENT_SECRET:
            raise ValueError(
                "CRITICAL SECURITY VIOLATION: SECRET_KEY must be an explicit, "
                "non-development value of at least 32 characters in production."
            )
        if not self.MQTT_PASSWORD or not self.MQTT_PASSWORD.strip():
            raise ValueError(
                "CRITICAL SECURITY VIOLATION: MQTT_PASSWORD environment key must be "
                "explicitly provided in production."
            )
        if (
            not self.DATABASE_URL
            or not self.DATABASE_URL.strip()
            or self.DATABASE_URL == _DEVELOPMENT_DATABASE_URL
        ):
            raise ValueError(
                "CRITICAL ARCHITECTURAL VIOLATION: DATABASE_URL engine connection "
                "string must be explicitly set in production."
            )
        return self

    @property
    def is_production(self) -> bool:
        """Return true when either supported deployment context selects production."""
        return self.ENV == "production" or self.ENVIRONMENT == "production"


# Compatibility name used by the core-foundation test and integration surfaces.
AppSettings = Settings


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""
    return Settings()


settings = get_settings()

__all__ = ["AppSettings", "Settings", "get_settings", "settings"]
