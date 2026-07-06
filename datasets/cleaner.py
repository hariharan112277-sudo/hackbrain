"""
Industrial Telemetry Data Cleansing, Resampling & Anomaly Mitigation Module.
"""
import numpy as np
import pandas as pd
from datasets.logger import get_pipeline_logger
from datasets.config import pipeline_config

logger = get_pipeline_logger("cleaner")


class IndustrialDataCleaner:
    def __init__(self):
        self.z_thresh = pipeline_config.Z_SCORE_OUTLIER_THRESHOLD

    def purge_and_realign_telemetry(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies robust statistical adjustments and resamples irregular historical telemetry inputs."""
        if df.empty:
            logger.warning("Empty dataframe received inside cleansing workflow pipeline.")
            return df

        cleaned = df.copy()
        cleaned['timestamp'] = pd.to_datetime(cleaned['timestamp'])

        # Deduplicate sequential rows sharing exact time-domain signatures
        init_len = len(cleaned)
        cleaned = cleaned.drop_duplicates(subset=['timestamp', 'machine_id', 'sensor_id'])
        if len(cleaned) < init_len:
            logger.info(f"Dropped {init_len - len(cleaned)} exact temporal duplication matrix records.")

        # Mitigate communications dropouts by screening raw OPC Quality Standard Codes
        if 'quality_code' in cleaned.columns:
            invalid_mask = cleaned['quality_code'] != 192
            cleaned.loc[invalid_mask, 'measured_value'] = np.nan
            logger.info(f"Isolated {invalid_mask.sum()} elements violating OPC-DA 'Good Quality' standard metrics.")

        # Clean physical sensor measurements using Modified Z-Score calculations
        for sensor in cleaned['sensor_id'].unique():
            s_mask = cleaned['sensor_id'] == sensor
            vals = cleaned.loc[s_mask, 'measured_value']
            valid_vals = vals.dropna()
            if valid_vals.empty:
                continue
            median = valid_vals.median()
            mad = np.nanmedian(np.abs(valid_vals - median))
            if mad > 0:
                modified_z = 0.6745 * (vals - median) / mad
                outliers = np.abs(modified_z) > self.z_thresh
                outliers = outliers.fillna(False)
                cleaned.loc[s_mask & outliers, 'measured_value'] = np.nan
                if outliers.sum() > 0:
                    logger.info(f"Isolated {outliers.sum()} anomalous physical measurement metrics for sensor tracking key: {sensor}")

        # Uniform alignment grid generation via pivot transformations
        try:
            pivoted = cleaned.pivot(index='timestamp', columns=['machine_id', 'sensor_id'], values='measured_value')
            rule = pipeline_config.RESAMPLE_RULE
            if rule == '1T':
                rule = '1min'
            resampled = pivoted.resample(rule, origin='start').mean()

            # Linearly interpolate data gaps up to the limits set in the configuration file
            final_df = resampled.interpolate(
                method=pipeline_config.INTERPOLATION_METHOD,
                limit=pipeline_config.MAX_GAP_INTERPOLATE_PERIODS
            ).bfill().ffill()

            # Unpivot to restore tabular schema structures
            try:
                restored = final_df.stack(level=['machine_id', 'sensor_id'], future_stack=True).reset_index()
            except TypeError:
                restored = final_df.stack(level=['machine_id', 'sensor_id']).reset_index()

            if 0 in restored.columns:
                restored.rename(columns={0: 'measured_value'}, inplace=True)
            elif '0' in restored.columns:
                restored.rename(columns={'0': 'measured_value'}, inplace=True)
            return restored
        except Exception as e:
            logger.warning(f"Pivot/resample realignment warning ({e}). Returning forward-filled cleaned dataframe.")
            return cleaned.sort_values('timestamp').ffill().bfill()
