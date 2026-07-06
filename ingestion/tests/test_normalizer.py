from ingestion.normalizer import EngineeringUnitNormalizer


def test_engineering_unit_normalizer_temperature_f_to_c():
    normalizer = EngineeringUnitNormalizer()
    payload = {
        "readings": {
            "temperature": {"value": 212.0, "unit": "F"}
        }
    }
    result = normalizer.process(payload)
    norm = result["_normalized_readings"]["temperature"]
    assert abs(norm["normalized_value"] - 100.0) < 0.001
    assert norm["normalized_unit"] == "CELSIUS"


def test_engineering_unit_normalizer_pressure_psi_to_bar():
    normalizer = EngineeringUnitNormalizer()
    payload = {
        "readings": {
            "pressure": {"value": 100.0, "unit": "PSI"}
        }
    }
    result = normalizer.process(payload)
    norm = result["_normalized_readings"]["pressure"]
    assert abs(norm["normalized_value"] - 6.895) < 0.01
    assert norm["normalized_unit"] == "BAR"


def test_engineering_unit_normalizer_speed_hz_to_rpm():
    normalizer = EngineeringUnitNormalizer()
    payload = {
        "readings": {
            "speed": {"value": 50.0, "unit": "Hz"}
        }
    }
    result = normalizer.process(payload)
    norm = result["_normalized_readings"]["speed"]
    assert abs(norm["normalized_value"] - 3000.0) < 0.001
    assert norm["normalized_unit"] == "RPM"
