"""Validated application configuration with explicit production boundaries."""
from __future__ import annotations
from functools import lru_cache
from typing import Annotated, List, Optional
from pydantic import Field, field_validator, model_validator, AliasChoices
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_DEVELOPMENT_SECRET = "development-only-secret-key-change-before-deploying"
_DEVELOPMENT_DATABASE_URL = "sqlite:///./iob_development.db"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore", validate_default=True)
    APP_NAME: str = "Industrial Operating Brain"
    APP_VERSION: str = "5.0.0"
    PROJECT_NAME: str = "Enterprise Backend Core"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    ENV: str = Field("development", validation_alias=AliasChoices("ENV", "IOB_ENV_MODE"))
    ENVIRONMENT: str = "local"
    USE_STUB_REPOSITORIES: bool = True
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = Field(_DEVELOPMENT_SECRET, validation_alias=AliasChoices("SECRET_KEY", "IOB_JWT_SECRET_KEY"))
    JWT_SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 12
    BCRYPT_ROUNDS: int = 12
    # NoDecode lets the validator accept both documented comma-separated
    # values and JSON arrays from environment sources.
    CORS_ORIGINS: Annotated[List[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"]
    )
    ALLOWED_HOSTS: Annotated[List[str], NoDecode] = Field(default_factory=lambda: ["*"])
    DATABASE_URL: Optional[str] = Field(_DEVELOPMENT_DATABASE_URL, validation_alias=AliasChoices("DATABASE_URL", "IOB_POSTGRES_DSN"))
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    MQTT_BROKER_HOST: str = Field("localhost", validation_alias=AliasChoices("MQTT_BROKER_HOST", "IOB_MQTT_BROKER_HOST"))
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_CLIENT_ID: str = "iob-backend"
    MQTT_KEEPALIVE: int = 60
    MQTT_TLS_ENABLED: bool = False
    IOB_MQTT_URL: str = "mqtt://localhost:1883"
    IOB_TOPIC_PREFIX: str = "industrial/iob"
    AI_GATEWAY_KEY: Optional[str] = Field(None, validation_alias=AliasChoices("AI_GATEWAY_KEY", "IOB_AI_GATEWAY_KEY"))
    DEFAULT_PAGE_LIMIT: int = 100
    MAX_PAGE_LIMIT: int = 100
    MAX_HISTORICAL_WINDOW_DAYS: int = 30
    ENABLE_REALTIME_STREAMING: bool = True
    ENFORCE_OPC_QUALITY_CHECKS: bool = True
    AI_GATEWAY_MAX_PAYLOAD_BYTES: int = 10 * 1024 * 1024
    WS_BROADCAST_BATCH_MS: int = 0
    WS_BROADCAST_BATCH_MAX: int = 50
    AUTH_COOKIE_ENABLED: bool = True
    AUTH_COOKIE_NAME: str = "iob_access_token"
    AUTH_COOKIE_SECURE: bool = False
    AUTH_COOKIE_SAMESITE: str = "lax"
    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_TIMEOUT: int = 30
    FRONTEND_URL: str = "http://localhost:3000"
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    JSON_LOGS: bool = True
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    ENABLE_AI_INTEGRATION: bool = True
    ENABLE_REALTIME_TELEMETRY: bool = True
    ENABLE_ALARM_NOTIFICATIONS: bool = True

    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_lists(cls, value):
        if isinstance(value, str):
            import json
            if value.strip().startswith("["):
                return json.loads(value)
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @field_validator("ENV", "ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, value): return str(value).strip().lower()

    @model_validator(mode="after")
    def validate_production_boundaries(self):
        if self.is_production:
            if len(self.SECRET_KEY.strip()) < 32 or self.SECRET_KEY == _DEVELOPMENT_SECRET:
                raise ValueError("IOB_JWT_SECRET_KEY/SECRET_KEY must be at least 32 random characters in production")
            if not self.DATABASE_URL or self.DATABASE_URL == _DEVELOPMENT_DATABASE_URL:
                raise ValueError("IOB_POSTGRES_DSN/DATABASE_URL is required in production")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("Wildcard CORS origins are forbidden in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.ENV == "production" or self.ENVIRONMENT == "production"

AppSettings = Settings
@lru_cache
def get_settings() -> Settings: return Settings()
settings = get_settings()
__all__ = ["AppSettings", "Settings", "get_settings", "settings"]
