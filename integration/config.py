"""
Integration Layer Configuration Models.

The project prefers `pydantic-settings` when available. A lightweight Pydantic
fallback is provided so contract-only imports such as `integration.backend_contracts`
remain executable in minimal validation environments where optional runtime
settings dependencies have not been installed yet.
"""
from pydantic import BaseModel, ConfigDict, Field

try:  # pragma: no cover - depends on optional runtime package availability
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:  # contract/test environment fallback
    class BaseSettings(BaseModel):
        model_config = ConfigDict(extra="ignore", populate_by_name=True)

    def SettingsConfigDict(**kwargs):
        return ConfigDict(**{k: v for k, v in kwargs.items() if k in {"extra", "populate_by_name"}})


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
        extra="ignore",
        populate_by_name=True,
    )


integration_config = IntegrationSettings()
