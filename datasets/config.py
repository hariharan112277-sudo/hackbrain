"""
Configuration Specification Subspace Module for Data Ingestion & Cleansing Rules.
"""
from typing import Dict, Any, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class DataPipelineSettings(BaseSettings):
    """Strongly-typed parameters for data preparation pipeline execution."""
    DATABASE_URI: str = Field(default="postgresql://postgres:postgres@localhost:5432/iob_db")
    OUTPUT_BASE_DIR: str = Field(default="./data_output")
    DATASET_VERSION: str = Field(default="v1.0.0")

    # Cleaning Configurations
    Z_SCORE_OUTLIER_THRESHOLD: float = 3.5
    RESAMPLE_RULE: str = "1min"  # 1-Minute fixed frequency resampling window
    INTERPOLATION_METHOD: str = "linear"
    MAX_GAP_INTERPOLATE_PERIODS: int = 5

    # Labeling parameters
    RUL_MAX_LIMIT_DAYS: float = 30.0
    PREDICTIVE_FAILURE_WINDOW_MINUTES: int = 120

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


pipeline_config = DataPipelineSettings()
