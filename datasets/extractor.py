"""
Database Extraction Layer utilizing SQLAlchemy read-only query streams.
"""
import pandas as pd
from typing import Any
from datasets.logger import get_pipeline_logger

logger = get_pipeline_logger("extractor")


class IndustrialDataExtractor:
    def __init__(self, engine_session: Any):
        self.session = engine_session

    def _get_connection(self) -> Any:
        if hasattr(self.session, "connection") and callable(getattr(self.session, "connection")):
            try:
                return self.session.connection()
            except Exception:
                return self.session
        return self.session

    def extract_telemetry_window(self, start_time: str, end_time: str) -> pd.DataFrame:
        """Stream historical timeseries hypertable segments efficiently."""
        logger.info(f"Extracting historical telemetry interval window: {start_time} -> {end_time}")
        query = f"""
            SELECT id, timestamp, machine_id, sensor_id, measured_value, quality_code, alarm_status
            FROM telemetry
            WHERE timestamp >= '{start_time}' AND timestamp <= '{end_time}'
            ORDER BY timestamp ASC;
        """
        try:
            return pd.read_sql_query(query, con=self._get_connection())
        except Exception as e:
            logger.warning(f"Error querying telemetry window: {e}. Returning empty DataFrame.")
            return pd.DataFrame(columns=['id', 'timestamp', 'machine_id', 'sensor_id', 'measured_value', 'quality_code', 'alarm_status'])

    def extract_alarm_history(self) -> pd.DataFrame:
        """Extract historical alarm sequence log matrix arrays."""
        logger.info("Extracting raw alarm record logs mapping matrices.")
        query = "SELECT id, machine_id, sensor_id, severity, state, trigger_timestamp, clear_timestamp, trigger_value FROM alarms;"
        try:
            return pd.read_sql_query(query, con=self._get_connection())
        except Exception as e:
            logger.warning(f"Error querying alarms: {e}. Returning empty DataFrame.")
            return pd.DataFrame(columns=['id', 'machine_id', 'sensor_id', 'severity', 'state', 'trigger_timestamp', 'clear_timestamp', 'trigger_value'])

    def extract_maintenance_logs(self) -> pd.DataFrame:
        """Extract baseline operational maintenance schedules."""
        logger.info("Extracting maintenance events execution database fields.")
        query = "SELECT id, machine_id, technician_id, maintenance_type, scheduled_time, start_time, end_time, status FROM maintenance_logs;"
        try:
            return pd.read_sql_query(query, con=self._get_connection())
        except Exception as e:
            logger.warning(f"Error querying maintenance logs: {e}. Returning empty DataFrame.")
            return pd.DataFrame(columns=['id', 'machine_id', 'technician_id', 'maintenance_type', 'scheduled_time', 'start_time', 'end_time', 'status'])

    def extract_failures_ledger(self) -> pd.DataFrame:
        """Extract validated equipment downtime failure tracking tables."""
        logger.info("Extracting absolute raw historical verified operational failures dataset ledger rows.")
        query = "SELECT id, timestamp, machine_id, failure_type, category, severity, operating_hours FROM machine_failures;"
        try:
            return pd.read_sql_query(query, con=self._get_connection())
        except Exception as e:
            logger.warning(f"Table machine_failures not accessible ({e}). Attempting fallback extraction from alarms.")
            try:
                fallback_query = """
                    SELECT id, trigger_timestamp as timestamp, machine_id, threshold_violated as failure_type,
                           'MECHANICAL' as category, severity, 0.0 as operating_hours
                    FROM alarms WHERE state = 'ACTIVE' OR severity IN ('HIGH', 'CRITICAL');
                """
                return pd.read_sql_query(fallback_query, con=self._get_connection())
            except Exception:
                return pd.DataFrame(columns=['id', 'timestamp', 'machine_id', 'failure_type', 'category', 'severity', 'operating_hours'])
