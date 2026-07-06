"""
Multi-Scale Temporal Windows Cumulative Summary Aggregator.
"""
import pandas as pd
from datasets.logger import get_pipeline_logger

logger = get_pipeline_logger("aggregator")


class TimeSeriesAggregator:
    @staticmethod
    def calculate_rolling_features(df: pd.DataFrame, window_sizes: list = [5, 15, 60]) -> pd.DataFrame:
        """Computes rolling summary statistics across dynamic user-configured time windows."""
        logger.info(f"Generating statistical rolling feature transformations across window intervals: {window_sizes}T")

        if df.empty or 'measured_value' not in df.columns:
            return df

        group_cols = [col for col in ['machine_id', 'sensor_id'] if col in df.columns]
        df_out = df.sort_values(group_cols + ['timestamp']).copy() if group_cols and 'timestamp' in df.columns else df.copy()

        for w in window_sizes:
            if group_cols:
                group = df_out.groupby(group_cols)['measured_value']
                df_out[f'rolling_mean_{w}m'] = group.transform(lambda x: x.rolling(window=w, min_periods=1).mean())
                df_out[f'rolling_std_{w}m'] = group.transform(lambda x: x.rolling(window=w, min_periods=1).std()).fillna(0.0)
                df_out[f'rolling_max_{w}m'] = group.transform(lambda x: x.rolling(window=w, min_periods=1).max())
                df_out[f'rolling_min_{w}m'] = group.transform(lambda x: x.rolling(window=w, min_periods=1).min())
            else:
                s = df_out['measured_value']
                df_out[f'rolling_mean_{w}m'] = s.rolling(window=w, min_periods=1).mean()
                df_out[f'rolling_std_{w}m'] = s.rolling(window=w, min_periods=1).std().fillna(0.0)
                df_out[f'rolling_max_{w}m'] = s.rolling(window=w, min_periods=1).max()
                df_out[f'rolling_min_{w}m'] = s.rolling(window=w, min_periods=1).min()

        return df_out
