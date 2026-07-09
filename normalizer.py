"""
Engineering Unit Normalizer Stage for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: ISA-95 Part 2 Measurement Units Standardization.
"""

import logging
from typing import Dict, Any, Callable, Optional
from .exceptions import UnitConversionException

logger = logging.getLogger("iob.normalizer")


class EngineeringUnitNormalizer:
    """Normalizes physical engineering units into standard SI formats using standard scaling formulas."""
    def __init__(self, matrix_cfg: Dict[str, Any] = None):
        self.matrix = matrix_cfg or {
            "TEMPERATURE": {
                "source_units": {"FAHRENHEIT": "CELSIUS", "F": "CELSIUS", "KELVIN": "CELSIUS"},
                "conversions": {
                    "FAHRENHEIT": "lambda x: (x - 32) * 5.0 / 9.0",
                    "F": "lambda x: (x - 32) * 5.0 / 9.0",
                    "KELVIN": "lambda x: x - 273.15"
                },
                "target_unit": "CELSIUS",
                "output_precision": 2
            },
            "PRESSURE": {
                "source_units": {"PSI": "BAR", "KPA": "BAR"},
                "conversions": {
                    "PSI": "lambda x: x * 0.0689476",
                    "KPA": "lambda x: x / 100.0"
                },
                "target_unit": "BAR",
                "output_precision": 3
            },
            "SPEED": {
                "source_units": {"HZ": "RPM"},
                "conversions": {"HZ": "lambda x: x * 60.0"},
                "target_unit": "RPM",
                "output_precision": 1
            }
        }

    def _find_rules(self, topic_str: str, measurement_str: str) -> Optional[Dict[str, Any]]:
        cand1 = topic_str.split("/")[-1].upper() if topic_str else ""
        cand2 = measurement_str.upper()
        for key, rules in self.matrix.items():
            if key == cand1 or key == cand2 or key in cand1 or key in cand2 or cand1 in key:
                return rules
        return None

    def normalize_inplace(self, payload: Dict[str, Any]) -> None:
        topic_str = str(payload.get("topic", ""))
        measurement_str = str(payload.get("measurement", ""))
        current_unit = str(payload.get("unit", "")).upper()

        domain_rules = self._find_rules(topic_str, measurement_str)
        if domain_rules and current_unit != domain_rules["target_unit"] and current_unit in domain_rules["source_units"]:
            raw_value = float(payload["value"])
            expression_string = domain_rules["conversions"][current_unit]
            try:
                conversion_formula: Callable[[float], float] = eval(expression_string)
                normalized_value = conversion_formula(raw_value)
                precision = domain_rules["output_precision"]
                payload["value"] = round(normalized_value, precision)
                payload["unit"] = domain_rules["target_unit"]
                logger.debug(f"Normalized unit scale: {raw_value} {current_unit} -> {payload['value']} {payload['unit']}")
            except Exception as ex:
                raise UnitConversionException(f"Failed to execute engineering unit conversion: {str(ex)}")

        readings = payload.get("readings", {})
        if isinstance(readings, dict):
            normalized: Dict[str, Any] = {}
            for metric, item in readings.items():
                if isinstance(item, dict):
                    raw_val = float(item.get("value", 0.0))
                    raw_unit = str(item.get("unit", "")).upper()
                else:
                    raw_val = float(item)
                    raw_unit = ""

                m_upper = metric.upper()
                if m_upper in self.matrix and raw_unit in self.matrix[m_upper]["source_units"]:
                    fn = eval(self.matrix[m_upper]["conversions"][raw_unit])
                    norm_val = round(fn(raw_val), self.matrix[m_upper]["output_precision"])
                    norm_unit = self.matrix[m_upper]["target_unit"]
                elif metric.lower() == "temperature" and raw_unit == "F":
                    norm_val = round((raw_val - 32.0) * 5.0 / 9.0, 2)
                    norm_unit = "CELSIUS"
                elif metric.lower() == "vibration" and raw_unit == "IN/S":
                    norm_val = round(raw_val * 25.4, 3)
                    norm_unit = "MM/S"
                else:
                    norm_val, norm_unit = raw_val, raw_unit

                normalized[metric] = {
                    "raw_value": raw_val,
                    "normalized_value": norm_val,
                    "raw_unit": raw_unit,
                    "normalized_unit": norm_unit,
                    "quality": "GOOD"
                }
            payload["_normalized_readings"] = normalized

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.normalize_inplace(payload)
        return payload
