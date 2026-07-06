"""
IOB Industrial Database Configuration Engine.
Responsible for reading configuration profiles, validating environment variables,
and computing connection string parameterizations.
"""

import os
from typing import Any, Dict, Optional
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """Strongly-typed Database connection settings."""
    DB_HOST: str = Field(default="localhost", alias="POSTGRES_HOST")
    DB_PORT: int = Field(default=5432, alias="POSTGRES_PORT")
    DB_USER: str = Field(default="iob_admin", alias="POSTGRES_USER")
    DB_PASSWORD: str = Field(default="iob_secure_pass", alias="POSTGRES_PASSWORD")
    DB_NAME: str = Field(default="iob_industrial", alias="POSTGRES_DB")
    DB_SCHEMA: str = Field(default="industrial", alias="POSTGRES_SCHEMA")

    # Connection Pool Properties
    POOL_SIZE: int = Field(default=20, alias="DB_POOL_SIZE")
    MAX_OVERFLOW: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    POOL_TIMEOUT: float = Field(default=30.0, alias="DB_POOL_TIMEOUT")
    POOL_RECYCLE: int = Field(default=1800, alias="DB_POOL_RECYCLE")

    # Resilience & Connection Mechanics
    CONNECT_RETRY_LIMIT: int = Field(default=5, alias="DB_RETRY_LIMIT")
    CONNECT_RETRY_DELAY: float = Field(default=2.0, alias="DB_RETRY_DELAY")
    SSL_MODE: str = Field(default="prefer", alias="DB_SSL_MODE")

    # Application Logging Toggle
    LOG_LEVEL: str = Field(default="INFO", alias="DB_LOG_LEVEL")

    # Testing overrides
    TEST_DB_URL: Optional[str] = Field(default=None, alias="TEST_DB_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def sqlalchemy_url(self) -> str:
        """Computes a synchronized database target DSN string."""
        if self.TEST_DB_URL:
            return self.TEST_DB_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?sslmode={self.SSL_MODE}"


def load_config_from_yaml(yaml_path: str) -> Dict[str, Any]:
    """Helper fallback to extract setup properties from yaml structures."""
    if not os.path.exists(yaml_path):
        return {}
    with open(yaml_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f) or {}
    return config_data.get("database", {})


# Global configuration instance
db_settings = DatabaseSettings()
