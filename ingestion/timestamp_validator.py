"""
Chrono Timestamp Validator Stage for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: IEC 62443 Temporal Integrity, ISO 8601 Timestamp Validation.
"""

import datetime
import logging
from typing import Dict, Any
from .exceptions import ClockDriftViolationException

logger = logging.getLogger("iob.chrono")


class ChronoTimestampValidator:
    """Validates incoming ISO-8601 strings and monitors clock drift threshold limits."""
    def __init__(self, future_limit_sec: float = 5.0, past_limit_sec: float = 86400.0, max_future_drift_seconds: float = None, max_past_drift_seconds: float = None):
        self.future_limit = max_future_drift_seconds if max_future_drift_seconds is not None else future_limit_sec
        self.past_limit = max_past_drift_seconds if max_past_drift_seconds is not None else past_limit_sec

    def assert_timestamp_bounds(self, payload: Dict[str, Any]) -> None:
        ts_str = payload.get("timestamp")
        if ts_str is None:
            raise ClockDriftViolationException("Timestamp field is missing from payload.")

        try:
            if isinstance(ts_str, (int, float)):
                parsed_dt = datetime.datetime.utcfromtimestamp(float(ts_str))
                epoch_val = float(ts_str)
            else:
                clean_ts = str(ts_str).rstrip("Z")
                parsed_dt = datetime.datetime.fromisoformat(clean_ts)
                if parsed_dt.tzinfo is not None:
                    parsed_dt_naive = parsed_dt.replace(tzinfo=None)
                else:
                    parsed_dt_naive = parsed_dt
                parsed_dt = parsed_dt_naive
                epoch_val = (parsed_dt_naive - datetime.datetime(1970, 1, 1)).total_seconds()
        except ValueError:
            raise ClockDriftViolationException(f"Invalid timestamp string format: {ts_str}")

        now = datetime.datetime.utcnow()
        drift_delta = (now - parsed_dt).total_seconds()

        if drift_delta < -self.future_limit:
            raise ClockDriftViolationException(f"Future timestamp drift rejected: {ts_str} (Drift: {drift_delta}s)")

        if drift_delta > self.past_limit:
            raise ClockDriftViolationException(f"Stale packet expiration limit reached: {ts_str} (Drift: {drift_delta}s)")

        payload["_parsed_timestamp"] = epoch_val

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.assert_timestamp_bounds(payload)
        return payload
