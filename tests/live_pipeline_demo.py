"""
Live end-to-end pipeline demo (no broker / no PG required).

Drives the entire Stage 1 pipeline:

    Simulator -> JSON wire payload -> Pydantic Validator
                                      -> NormalizationEngine (UNS parsing)
                                      -> Repository (mock save, prints rows)

Proves the whole flow works as a unit, with the actual YAML config
loaded from ``config/simulator_config.yaml``.

Run:    python tests/live_pipeline_demo.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config_loader import ConfigLoader
from src.simulator.core_simulator import IndustrialSimulator
from src.ingestion.mqtt_client import TelemetryIngestionWorker
from src.database.telemetry_repository import TelemetryRepository


def main() -> int:
    print("=" * 70)
    print("IOB Data Engine - Stage 1 LIVE END-TO-END DEMO")
    print("(No broker / no PG needed - uses mocks)")
    print("=" * 70)

    # 1. Load real config
    cfg = ConfigLoader.load_yaml("config/simulator_config.yaml")
    print(f"\n[1] Loaded YAML: version={cfg['version']}, "
          f"broker={cfg['broker']['host']}:{cfg['broker']['port']}")
    print(f"    Devices: {len(cfg['devices'])}")
    for d in cfg["devices"]:
        print(f"      - {d['id']} ({d['type']}, {len(d['metrics'])} metrics)")

    # 2. Patch paho-mqtt to capture publishes without a real broker
    print("\n[2] Starting simulator (1 tick per device)…")
    captured_payloads = []

    import paho.mqtt.client as mqtt
    real_publish = mqtt.Client.publish

    def _capture_publish(self, topic, payload=None, qos=0, retain=False,
                         properties=None):
        captured_payloads.append({"topic": topic, "payload": payload,
                                  "qos": qos})
        # Return a mock result with rc=0 (success)
        result = MagicMock()
        result.rc = mqtt.MQTT_ERR_SUCCESS
        result.is_published = lambda: True
        result.wait_for_publish = lambda timeout=None: True
        return result

    mqtt.Client.publish = _capture_publish

    sim = IndustrialSimulator(cfg)
    sim.running = True

    # Drive exactly one tick per device without sleeping
    def _stop_after_first_sleep(_secs, _keep):
        sim.running = False

    import src.simulator.core_simulator as core_sim
    orig_sleep = core_sim._interruptible_sleep
    core_sim._interruptible_sleep = _stop_after_first_sleep
    try:
        for d in sim.devices:
            sim.running = True  # re-arm for next device
            core_sim._interruptible_sleep = _stop_after_first_sleep
            sim._device_loop(d)
    finally:
        mqtt.Client.publish = real_publish

    print(f"    Captured {len(captured_payloads)} MQTT publishes\n")

    # 3. Drive the ingestion worker on each captured payload
    print("[3] Driving ingestion worker (Pydantic + Normalization):\n")
    repo = MagicMock(spec=TelemetryRepository)
    worker = TelemetryIngestionWorker(cfg["broker"], repo)

    for i, pub in enumerate(captured_payloads, 1):
        msg = MagicMock()
        msg.topic = pub["topic"]
        msg.payload = (pub["payload"]
                       if isinstance(pub["payload"], (bytes, bytearray))
                       else pub["payload"].encode("utf-8"))
        worker._on_message(None, None, msg)

        saved = repo.save_telemetry.call_args_list[-1].args[0]
        print(f"    #{i:>2} topic={pub['topic']}")
        raw = json.loads(pub["payload"]) if isinstance(pub["payload"], str) \
            else json.loads(pub["payload"].decode("utf-8"))
        print(f"         device={raw['device_id']}")
        print(f"         ts    ={datetime.fromtimestamp(raw['timestamp'], tz=timezone.utc).isoformat()}")
        print(f"         metrics({len(raw['telemetry'])})={list(raw['telemetry'].keys())}")
        print(f"         NORMALIZED -> site={saved['site_id']} "
              f"area={saved['area_id']}")
        print(f"                       timestamp_utc={saved['timestamp_utc']}")
        print(f"                       metrics={saved['metrics']}")
        print()

    print("=" * 70)
    print(f"Pipeline summary: received={worker.stats['received']}, "
          f"validated={worker.stats['validated']}, "
          f"persisted={worker.stats['persisted']}, "
          f"errors={worker.stats['errors']}")
    print("=" * 70)
    print()
    print("Next steps for live deployment:")
    print("  1. Start broker: docker run -p 1883:1883 eclipse-mosquitto:2")
    print("  2. Start PG:     docker run -p 5432:5432 \\")
    print("                       -e POSTGRES_DB=iob_db \\")
    print("                       -e POSTGRES_USER=postgres \\")
    print("                       -e POSTGRES_PASSWORD=postgres postgres:15")
    print("  3. Run:          python main_stage1.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
