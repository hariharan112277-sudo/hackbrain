"""
Operational Quality Checker Stage for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: ISA-95 Part 2 Data Quality Codes, Operational Bounds Verification.
"""

from typing import Dict, Any, Optional
from .constants import QUALITY_GOOD, QUALITY_CLAMPED
from .exceptions import QualityCheckException


class OperationalQualityChecker:
    """Evaluates raw field measurements against physical boundary limits."""
    def __init__(self, limits_config: Optional[Dict[str, Any]] = None, strict_mode: bool = False):
        self.limits = limits_config or {
            "critical_temperature_upper_bound": 150.0,
            "critical_pressure_upper_bound": 250.0,
            "critical_current_upper_bound": 120.0,
            "invalid_vibration_g_limit": 15.0
        }
        self.strict_mode = strict_mode

    def evaluate_quality_score(self, payload: Dict[str, Any]) -> float:
        base_quality = payload.get("quality", QUALITY_GOOD)
        topic_str = str(payload.get("topic", ""))
        measurement_type = topic_str.split("/")[-1].upper() if topic_str else str(payload.get("measurement", "")).upper()
        try:
            value = float(payload.get("value", 0.0))
        except (ValueError, TypeError):
            value = 0.0

        if base_quality == "BAD_TIMEOUT":
            return 0.0

        score = 100.0

        if base_quality == QUALITY_CLAMPED:
            score -= 30.0

        if measurement_type == "TEMPERATURE" and value > self.limits.get("critical_temperature_upper_bound", 150.0):
            score -= 50.0
            if self.strict_mode:
                raise QualityCheckException(f"violates quality boundary rule: {value}")
        elif measurement_type == "PRESSURE" and (value > self.limits.get("critical_pressure_upper_bound", 250.0) or value < 0):
            score -= 50.0
            if self.strict_mode:
                raise QualityCheckException(f"violates quality boundary rule: {value}")

        readings = payload.get("readings", {})
        if isinstance(readings, dict) and self.strict_mode:
            for k, v in readings.items():
                val = float(v.get("value", v)) if isinstance(v, dict) else float(v)
                if k.lower() == "pressure" and (val < 0 or val > 250.0):
                    raise QualityCheckException(f"violates quality boundary rule: {val}")

        return max(0.0, score)

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        score = self.evaluate_quality_score(payload)
        payload["quality_score"] = score
        overall_quality = payload.get("quality", QUALITY_GOOD)

        readings = payload.get("readings")
        if isinstance(readings, dict):
            for k, v in readings.items():
                if isinstance(v, dict):
                    val = float(v.get("value", 0.0))
                    qual = v.get("quality", QUALITY_GOOD)
                else:
                    val = float(v)
                    qual = QUALITY_GOOD

                limit = self.limits.get(f"critical_{k.lower()}_upper_bound", 150.0)
                if val > limit or val < 0:
                    qual = "UNCERTAIN" if not self.strict_mode else "BAD"
                    if self.strict_mode:
                        raise QualityCheckException(f"violates quality boundary rule: {val}")
                    overall_quality = qual

                if isinstance(v, dict):
                    v["quality"] = qual
                else:
                    readings[k] = {"value": val, "quality": qual}

        payload["quality"] = overall_quality
        payload["_overall_quality"] = overall_quality
        return payload
