"""
Application Configuration Management
Phase 5: Centralized configuration with environment-based settings.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Industrial Operating Brain"
    APP_VERSION: str = "5.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = Field(..., description="Secret key for JWT signing")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 12
    BCRYPT_ROUNDS: int = 12

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )

    # Database (Member 2 Integration)
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis (Caching & Sessions)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5

    # MQTT (Member 2 IoT Integration)
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_CLIENT_ID: str = "iob-backend"
    MQTT_KEEPALIVE: int = 60
    MQTT_TLS_ENABLED: bool = False

    # Member 3 AI Service
    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_TIMEOUT: int = 30
    AI_ANOMALY_ENDPOINT: str = "/predict/anomaly"
    AI_RUL_ENDPOINT: str = "/predict/rul"
    AI_HEALTH_ENDPOINT: str = "/health"

    # Member 4 Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    # Feature Flags
    ENABLE_AI_INTEGRATION: bool = True
    ENABLE_REALTIME_TELEMETRY: bool = True
    ENABLE_ALARM_NOTIFICATIONS: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()