from ingestion.metadata_enricher import StaticAssetMetadataEnricher


def test_metadata_enricher_known_asset():
    enricher = StaticAssetMetadataEnricher()
    payload = {
        "asset_id": "turbine-01",
        "topic": "site1/area1/line1/turbine-01/telemetry"
    }
    result = enricher.process(payload)
    assert result["_asset_metadata"]["manufacturer"] == "General Electric"
    assert result["_isa95_hierarchy"]["equipment"] == "turbine-01"


def test_metadata_enricher_unknown_asset_from_topic():
    enricher = StaticAssetMetadataEnricher()
    payload = {
        "asset_id": "motor-99",
        "topic": "plant-delhi/assembly/line-4/motor-99/telemetry"
    }
    result = enricher.process(payload)
    assert result["_isa95_hierarchy"]["site"] == "plant-delhi"
    assert result["_isa95_hierarchy"]["area"] == "assembly"
    assert result["_isa95_hierarchy"]["line"] == "line-4"
