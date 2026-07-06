"""
IOB Phase 3 - Telemetry Builder

Constructs compliant Phase 1 standardized JSON telemetry data envelopes.
"""

from typing import Any, Dict

from machine import MachineInstance
from sensor import SensorSimulator
from utils import utcnow_iso


class TelemetryBuilder:
    """
    Constructs compliant Phase 1 standardized JSON telemetry data envelopes.
    """

    @staticmethod
    def generate_json_envelope(
        factory_meta: Dict[str, str],
        machine: MachineInstance,
        sensor: SensorSimulator,
    ) -> Dict[str, Any]:
        """
        Generates standard structural tracking schemas for time-series parsing.
        """
        machine_stub = machine.machine_id.split("_")[-1].lower()
        return {
            "timestamp": utcnow_iso(),
            "asset_id": sensor.sensor_id,
            "machine_id": machine.machine_id,
            "sensor_id": sensor.sensor_id,
            "topic": (
                f"{factory_meta['enterprise'].lower()}/"
                f"{factory_meta['site'].lower()}/"
                f"{factory_meta['plant'].lower()}/"
                f"{machine.production_line.lower()}/"
                f"{machine_stub}/telemetry/{sensor.type.lower()}"
            ),
            "measurement": sensor.name.replace(" ", "_").lower(),
            "value": sensor.current_value,
            "unit": sensor.unit,
            "quality": sensor.quality,
            "sequence_number": sensor.sequence_number,
            "gateway_id": f"{factory_meta['site']}_{factory_meta['plant']}_GW01",
            "site_id": factory_meta["site"],
            "plant_id": factory_meta["plant"],
            "line_id": machine.production_line,
            "processing_status": "RAW",
            "metadata": {
                "machine_type": machine.type,
                "operating_hours": round(machine.operating_hours, 4),
                "machine_state": machine.current_state,
            },
        }
