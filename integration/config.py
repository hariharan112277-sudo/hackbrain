"""
Integration Layer Configuration Models.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class IntegrationSettings(BaseSettings):
    """Strongly-typed settings mapped via environment variables for Member 1."""
    MQTT_BROKER_URL: str = Field(default="mqtt://localhost:1883", alias="IOB_MQTT_URL")
    MQTT_TOPIC_PREFIX: str = Field(default="industrial/iob", alias="IOB_TOPIC_PREFIX")

    DEFAULT_PAGE_LIMIT: int = Field(default=100, ge=1, le=1000)
    MAX_HISTORICAL_WINDOW_DAYS: int = Field(default=30, gt=0)

    ENABLE_REALTIME_STREAMING: bool = True
    ENFORCE_OPC_QUALITY_CHECKS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


integration_config = IntegrationSettings()
