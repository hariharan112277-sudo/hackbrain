import pytest
from ingestion.exceptions import QualityCheckException
from ingestion.quality_checker import OperationalQualityChecker


def test_quality_checker_normal_bounds():
    checker = OperationalQualityChecker(strict_mode=False)
    payload = {
        "readings": {
            "temperature": {"value": 85.0, "unit": "C"},
            "vibration": 4.2
        }
    }
    result = checker.process(payload)
    assert result["readings"]["temperature"]["quality"] == "GOOD"
    assert result["readings"]["vibration"]["quality"] == "GOOD"
    assert result["_overall_quality"] == "GOOD"


def test_quality_checker_out_of_bounds_non_strict():
    checker = OperationalQualityChecker(strict_mode=False)
    payload = {
        "readings": {
            "temperature": 1500.0  # exceeds max 150.0
        }
    }
    result = checker.process(payload)
    assert result["readings"]["temperature"]["quality"] in ("UNCERTAIN", "BAD")
    assert result["_overall_quality"] in ("UNCERTAIN", "BAD")


def test_quality_checker_out_of_bounds_strict():
    checker = OperationalQualityChecker(strict_mode=True)
    payload = {
        "readings": {
            "pressure": 350.0  # exceeds critical_pressure_upper_bound 250.0
        }
    }
    with pytest.raises(QualityCheckException) as exc_info:
        checker.process(payload)
    assert "violates quality boundary rule" in str(exc_info.value)
