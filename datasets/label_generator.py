"""
Retrospective Target Label Generation Engine for Predictive Modeling Tasks.
"""
import numpy as np
import pandas as pd
from datasets.logger import get_pipeline_logger
from datasets.config import pipeline_config

logger = get_pipeline_logger("label_generator")


class IndustrialLabelGenerator:
    @staticmethod
    def append_predictive_maintenance_labels(telemetry_df: pd.DataFrame, failures_df: pd.DataFrame) -> pd.DataFrame:
        """Generates failure classifications, binary status flags, and continuous remaining useful life values."""
        logger.info("Constructing downstream training matrix label variables.")

        output_df = telemetry_df.copy()
        output_df['failure_binary_target'] = 0
        output_df['failure_category_target'] = "NORMAL"
        output_df['remaining_useful_life_hours'] = pipeline_config.RUL_MAX_LIMIT_DAYS * 24.0

        if failures_df.empty or 'machine_id' not in output_df.columns or 'timestamp' not in output_df.columns:
            return output_df

        failures_sorted = failures_df.sort_values('timestamp')

        for idx, row in output_df.iterrows():
            m_id = row['machine_id']
            t_stamp = pd.to_datetime(row['timestamp'])

            m_failures = failures_sorted[(failures_sorted['machine_id'] == m_id) & (pd.to_datetime(failures_sorted['timestamp']) >= t_stamp)]

            if not m_failures.empty:
                next_failure = m_failures.iloc[0]
                time_delta = pd.to_datetime(next_failure['timestamp']) - t_stamp
                hours_to_fail = time_delta.total_seconds() / 3600.0

                output_df.at[idx, 'remaining_useful_life_hours'] = hours_to_fail

                if hours_to_fail <= (pipeline_config.PREDICTIVE_FAILURE_WINDOW_MINUTES / 60.0):
                    output_df.at[idx, 'failure_binary_target'] = 1
                    output_df.at[idx, 'failure_category_target'] = next_failure.get('failure_type', 'FAULT')

        return output_df
