"""
Static Asset Metadata Enricher Stage for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: ISA-95 Part 2 Asset Model Enrichment.
"""

import datetime
from typing import Dict, Any


class StaticAssetMetadataEnricher:
    """Enriches data structures with pipeline context execution traces."""
    def __init__(self, environment: str = "production", pipeline_version: str = "v4.0"):
        self.env = environment
        self.version = pipeline_version

    def enrich_envelope(self, payload: Dict[str, Any], score: float) -> None:
        payload["quality_score"] = score
        payload["pipeline_ingest_time"] = datetime.datetime.utcnow().isoformat() + "Z"
        payload["pipeline_version"] = self.version

        if "metadata" not in payload:
            payload["metadata"] = {}

        payload["metadata"].update({
            "environment": self.env,
            "data_source_bus": "EMQX_MQTT_V5"
        })

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        score = payload.get("quality_score", 100.0)
        self.enrich_envelope(payload, score)

        # Backwards compatibility helper attributes
        asset_id = str(payload.get("asset_id", "UNKNOWN"))
        topic = str(payload.get("topic", ""))
        parts = [p for p in topic.split("/") if p]
        site = parts[0] if len(parts) >= 4 else "SITE_DEFAULT"

        payload["_asset_metadata"] = {
            "manufacturer": "General Electric" if "turbine" in asset_id else "Standard",
            "serial_number": f"SN-{asset_id}"
        }
        payload["_isa95_hierarchy"] = {
            "enterprise": "IOB_CORP",
            "site": site,
            "area": parts[1] if len(parts) >= 4 else "AREA_DEFAULT",
            "line": parts[2] if len(parts) >= 4 else "LINE_DEFAULT",
            "equipment": asset_id
        }
        return payload
