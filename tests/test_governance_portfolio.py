"""
Platform Ownership Governance Portfolio Verification Suite.
Validates ADR 024 JSON Schema Contract V2 and checks existence of governance artifacts.
"""
import os
import json
import pytest
import jsonschema


def test_adr024_telemetry_contract_v2_schema():
    """Verifies ADR 024 Approved V1.1 Backward-Compatible Extension schema."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, "schemas", "iob_telemetry_contract_v2.json")
    assert os.path.exists(schema_path)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    valid_payload = {
        "metadata": {
            "schema_version": "1.1.0",
            "timestamp_iso": "2026-07-04T06:14:22Z"
        },
        "metrics": {
            "vibration_x": 4.12,
            "temperature_winding": 84.5
        }
    }
    jsonschema.validate(instance=valid_payload, schema=schema)

    # Invalid schema version should fail
    invalid_payload = dict(valid_payload)
    invalid_payload["metadata"] = {"schema_version": "9.9.9", "timestamp_iso": "2026-07-04T06:14:22Z"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_payload, schema=schema)


def test_governance_portfolio_documents_exist():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    portfolio_path = os.path.join(base_dir, "governance", "iob_governance_portfolio.md")
    assert os.path.exists(portfolio_path)
    with open(portfolio_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "IOB-GOV-2026-V1.0" in content
    assert "IOB-2026-INC-042" in content
    assert "ADR 024" in content
    assert "CR-2026-089" in content
    assert "Sec-04" in content
    assert "IOB-SOP-012" in content
    assert "ADR 025" in content
    assert "1.1.0-RC3" in content
    assert "ISA-95/ISA-88" in content
