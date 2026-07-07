"""
IOB Data Engine — Stage 1 main entry point.

Boots the full pipeline:

    1. Load YAML config (``config/simulator_config.yaml``).
    2. Connect to PostgreSQL and bootstrap the
       ``iob_normalized_telemetry`` table.
    3. Start the MQTT ingestion worker (subscribes to ``iob/uns/#``).
    4. Start the multi-threaded industrial simulator.

Run with::

    python main_stage1.py
    python main_stage1.py --config /path/to/simulator_config.yaml
    python main_stage1.py --no-simulator    # ingestion-only mode
    python main_stage1.py --no-database     # simulator-only mode
    python main_stage1.py --runtime 30      # bounded smoke test
    python main_stage1.py --project-root /path/to/hackbrain
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional

# Make ``src.*`` importable when running ``python main_stage1.py`` directly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config_loader import ConfigLoader
from src.simulator.core_simulator import IndustrialSimulator
from src.database.telemetry_repository import TelemetryRepository
from src.ingestion.mqtt_client import TelemetryIngestionWorker

logger = logging.getLogger("iob.main")


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _connect_database(config: dict):
    """
    Build a psycopg2 connection from config['database'] if present,
    otherwise from defaults.  Returns ``None`` if psycopg2 isn't
    installed or connection fails (we continue in simulator-only mode).
    """
    try:
        import psycopg2  # type: ignore
    except ImportError:
        logger.warning("psycopg2 not installed; running in simulator-only mode")
        return None

    db_cfg = config.get("database", {})
    conn_str_parts = []
    if "conn_str" in db_cfg:
        return psycopg2.connect(db_cfg["conn_str"])
    for k in ("dbname", "user", "password", "host", "port"):
        v = db_cfg.get(k)
        if v is None:
            continue
        if k == "password":
            conn_str_parts.append(f"password={v}")
        elif k == "port":
            conn_str_parts.append(f"port={int(v)}")
        else:
            conn_str_parts.append(f"{k}={v}")
    if not conn_str_parts:
        # Fallback to the Stage 1 hard-coded defaults from the spec
        return psycopg2.connect(
            "dbname=iob_db user=postgres password=postgres "
            "host=localhost port=5432"
        )
    return psycopg2.connect(" ".join(conn_str_parts))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="IOB Data Engine - Stage 1 "
                    "(Industrial Data Acquisition & Simulation)")
    parser.add_argument(
        "--config", type=str, default="config/simulator_config.yaml",
        help="Path to simulator_config.yaml")
    parser.add_argument(
        "--project-root", type=str, default=None,
        help="Existing project root (auto-discovered if omitted). "
             "Used for legacy config/* merge + integration bridge.")
    parser.add_argument(
        "--no-simulator", action="store_true",
        help="Disable the device simulator (ingestion-only mode).")
    parser.add_argument(
        "--no-database", action="store_true",
        help="Disable the PostgreSQL persistence (simulator-only mode).")
    parser.add_argument(
        "--runtime", type=int, default=0,
        help="If >0, exit cleanly after this many seconds (smoke test).")
    parser.add_argument(
        "--log-level", type=str, default="INFO",
        help="Logging level (DEBUG/INFO/WARNING/ERROR).")
    args = parser.parse_args()

    setup_logging(args.log_level)

    print("[IOB STAGE 1] Starting Industrial Operating Brain "
          "Infrastructure...")

    # 1. Load YAML config (with legacy merge if project root provided)
    project_root = Path(args.project_root) if args.project_root \
        else Path(args.config).resolve().parent.parent.parent
    legacy_devices = project_root / "config" / "machines.yaml"
    legacy_sensors = project_root / "config" / "sensors.yaml"
    config = ConfigLoader.load_with_legacy(
        args.config,
        legacy_devices_path=str(legacy_devices)
            if legacy_devices.exists() else None,
        legacy_sensors_path=str(legacy_sensors)
            if legacy_sensors.exists() else None,
    )

    # 2. Connect to PostgreSQL and bootstrap table
    repo: Optional[TelemetryRepository] = None
    conn = None
    if not args.no_database:
        try:
            conn = _connect_database(config)
            repo = TelemetryRepository(conn)
            repo.init_tables()
        except Exception as exc:
            print(f"[DATABASE ERROR] Could not initialize persistence "
                  f"engine: {exc}. Running in simulator-only mode.")
            repo = None
            conn = None

    # 3. Start ingestion worker (only if we have a repository)
    worker: Optional[TelemetryIngestionWorker] = None
    if repo is not None:
        worker = TelemetryIngestionWorker(config["broker"], repo)
        worker.start()
    else:
        logger.info("Ingestion worker skipped (no database connection)")

    # 4. Start the simulator (unless --no-simulator)
    simulator: Optional[IndustrialSimulator] = None
    if not args.no_simulator:
        simulator = IndustrialSimulator(config)
        simulator.start()

    print("[IOB STAGE 1] Run loop active. Simulating and Ingesting IIoT "
          "stream data. Press Ctrl+C to terminate.")

    # 5. Main loop with optional bounded runtime
    deadline = time.time() + args.runtime if args.runtime > 0 else None
    try:
        while True:
            if deadline is not None and time.time() >= deadline:
                print(f"[IOB STAGE 1] Reached runtime={args.runtime}s; "
                      "shutting down.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("[IOB STAGE 1] Halting processes safely...")

    # 6. Graceful shutdown
    if simulator is not None:
        simulator.stop()
    if worker is not None:
        worker.stop()
    if conn is not None:
        try:
            conn.close()
        except Exception:  # pragma: no cover
            pass
    print("[IOB STAGE 1] Infrastructure successfully wound down.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
