"""
Telemetry Object Parser Stage for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: Strongly-typed data structure generation.
"""

from .models import StandardizedTelemetryModel, ISA95HierarchyModel, SensorMeasurementModel
from typing import Dict, Any


class TelemetryObjectParser:
    """Parses enriched dictionaries into strongly typed application models."""
    @staticmethod
    def map_to_frozen_model(p: Dict[str, Any]) -> StandardizedTelemetryModel:
        asset_id = str(p.get("asset_id", ""))
        topic = str(p.get("topic", ""))
        parts = [pt for pt in topic.split("/") if pt]
        isa95 = ISA95HierarchyModel(
            site=str(p.get("site_id", parts[0] if len(parts) >= 4 else "SITE_DEFAULT")),
            area=str(p.get("plant_id", parts[1] if len(parts) >= 4 else "AREA_DEFAULT")),
            line=str(p.get("line_id", parts[2] if len(parts) >= 4 else "LINE_DEFAULT")),
            equipment=asset_id
        )

        norm_readings = p.get("_normalized_readings", {})
        measurements: Dict[str, SensorMeasurementModel] = {}
        for metric, item in norm_readings.items():
            measurements[metric] = SensorMeasurementModel(
                metric_name=metric,
                raw_value=float(item.get("raw_value", 0.0)),
                normalized_value=float(item.get("normalized_value", 0.0)),
                raw_unit=str(item.get("raw_unit", "")),
                normalized_unit=str(item.get("normalized_unit", "")),
                quality=str(item.get("quality", "GOOD"))
            )

        measurement = str(p.get("measurement", ""))
        value = float(p.get("value", 0.0))
        unit = str(p.get("unit", ""))
        if measurement and measurement not in measurements:
            measurements[measurement] = SensorMeasurementModel(
                metric_name=measurement,
                raw_value=value,
                normalized_value=value,
                raw_unit=unit,
                normalized_unit=unit,
                quality=str(p.get("quality", "GOOD"))
            )

        return StandardizedTelemetryModel(
            timestamp=str(p.get("timestamp", "")),
            asset_id=asset_id,
            machine_id=str(p.get("machine_id", "MACH-DEFAULT")),
            sensor_id=str(p.get("sensor_id", "SENS-DEFAULT")),
            topic=topic,
            measurement=measurement,
            value=value,
            unit=unit,
            quality=str(p.get("quality", "GOOD")),
            sequence_number=int(p.get("sequence_number", 0)),
            gateway_id=str(p.get("gateway_id", "GW-DEFAULT")),
            site_id=str(p.get("site_id", "SITE-DEFAULT")),
            plant_id=str(p.get("plant_id", "PLANT-DEFAULT")),
            line_id=str(p.get("line_id", "LINE-DEFAULT")),
            quality_score=float(p.get("quality_score", 100.0)),
            pipeline_ingest_time=str(p.get("pipeline_ingest_time", "")),
            pipeline_version=str(p.get("pipeline_version", "v4.0")),
            metadata=p.get("metadata", {}),
            message_id=str(p.get("message_id", asset_id)),
            iso_timestamp=str(p.get("_iso_timestamp", p.get("timestamp", ""))),
            isa95_hierarchy=isa95,
            measurements=measurements,
            normalized_value=value,
            normalized_unit=unit
        )

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        model = self.map_to_frozen_model(payload)
        payload["_model"] = model
        return payload
