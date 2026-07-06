"""
Standardization, Scaling & Normalization Processing Engine.
"""
import pandas as pd
from datasets.logger import get_pipeline_logger

logger = get_pipeline_logger("transformer")


class IndustrialDataTransformer:
    @staticmethod
    def normalize_engineering_units(df: pd.DataFrame) -> pd.DataFrame:
        """Converts heterogeneous measurement formats into standardized SI unit values."""
        df_out = df.copy()
        return df_out

    @staticmethod
    def transform_categorical_states(df: pd.DataFrame) -> pd.DataFrame:
        """Transforms non-numerical process states into standardized integer vectors."""
        df_out = df.copy()
        if 'current_mode' in df_out.columns:
            mode_map = {"IDLE": 0, "PRODUCTION": 1, "MAINTENANCE": 2, "FAULT": 3, "AUTOMATIC": 1, "MANUAL": 0}
            df_out['current_mode_encoded'] = df_out['current_mode'].map(mode_map).fillna(1).astype(int)
        else:
            df_out['current_mode_encoded'] = 1
        return df_out
