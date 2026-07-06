from ingestion.models import TelemetryPayloadModel
from ingestion.parser import TelemetryObjectParser


def test_telemetry_object_parser_valid_dict():
    parser = TelemetryObjectParser()
    payload = {
        "message_id": "msg-999",
        "asset_id": "turbine-01",
        "topic": "site1/area1/line1/turbine-01/telemetry",
        "_parsed_timestamp": 1783000000.0,
        "_iso_timestamp": "2026-07-02T10:00:00Z",
        "_overall_quality": "GOOD",
        "_isa95_hierarchy": {
            "enterprise": "IOB_CORP",
            "site": "Site1",
            "area": "Area1",
            "line": "Line1",
            "equipment": "turbine-01"
        },
        "_asset_metadata": {
            "manufacturer": "GE",
            "asset_type": "Turbine"
        },
        "_normalized_readings": {
            "temperature": {
                "raw_value": 212.0,
                "normalized_value": 100.0,
                "raw_unit": "F",
                "normalized_unit": "C",
                "quality": "GOOD"
            }
        }
    }

    result = parser.process(payload)
    assert "_model" in result
    model = result["_model"]
    assert isinstance(model, TelemetryPayloadModel)
    assert model.message_id == "msg-999"
    assert model.measurements["temperature"].normalized_value == 100.0
    assert model.isa95_hierarchy.equipment == "turbine-01"
