"""
Generate a static sample of telemetry envelopes to ``sample_data/sample.jsonl``.

This is handy for feeding the Next.js digital-twin dashboard (``ethack`` repo)
or any downstream consumer when a live MQTT broker is not available.

Usage:
    python sample_data/generate_sample.py --count 200 --out sample_data/sample.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

# Make the simulator package importable when run directly
SIMULATOR_DIR = str(Path(__file__).resolve().parent.parent / "simulator")
if SIMULATOR_DIR not in sys.path:
    sys.path.insert(0, SIMULATOR_DIR)

from config import ConfigManager  # noqa: E402
from factory import FactorySimulatorOrchestrator  # noqa: E402
from telemetry import TelemetryBuilder  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Emit sample telemetry envelopes.")
    parser.add_argument("--count", type=int, default=100, help="number of envelopes")
    parser.add_argument(
        "--state",
        default="RUNNING",
        help="machine state to initialise twins in (default: RUNNING)",
    )
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "sample.jsonl"))
    args = parser.parse_args()

    # Build the orchestrator but drive it deterministically instead of in
    # real time so we can emit an exact number of envelopes quickly.
    orchestrator = FactorySimulatorOrchestrator()
    for machine in orchestrator.machines:
        machine.current_state = args.state
        machine.state_timer = 0.0
    now = __import__("time").time()

    envelopes = []
    emitted = 0
    step = 0.25  # 250 ms synthetic clock steps
    while emitted < args.count:
        now += step
        for machine in orchestrator.machines:
            active = machine.tick(now, step)
            for sensor in active:
                payload = TelemetryBuilder.generate_json_envelope(
                    orchestrator.factory_meta, machine, sensor
                )
                envelopes.append(payload)
                emitted += 1
                if emitted >= args.count:
                    break
            if emitted >= args.count:
                break

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        for envelope in envelopes:
            fh.write(json.dumps(envelope) + "\n")

    print(f"Wrote {len(envelops := envelopes)} envelopes to {out_path}")


if __name__ == "__main__":
    main()
