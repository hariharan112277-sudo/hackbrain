"""
Integration bridge: makes ``iob_data_engine`` interoperate with the
existing repository (which already has ``simulator/``, ``ingestion/``,
``database/``, ``integration/``, ``config/machines.yaml`` etc.).

* Auto-discovers the existing project root.
* Merges legacy ``config/machines.yaml`` + ``config/sensors.yaml`` into
  the Stage 1 device list (handled inside ``ConfigLoader.load_with_legacy``).
* Optionally reuses the existing PG connection wrapper if present.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger("iob.integration_bridge")


def find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    """Walk up looking for a directory containing ``simulator/`` AND ``ingestion/``."""
    current = Path(start) if start else Path(__file__).resolve()
    for _ in range(8):
        if (current / "simulator").is_dir() and (current / "ingestion").is_dir():
            return current
        current = current.parent
    return None


def add_project_root_to_path() -> Optional[Path]:
    """Add the existing project root to ``sys.path`` so bridge imports work."""
    root = find_project_root()
    if root and str(root) not in sys.path:
        sys.path.insert(0, str(root))
        logger.info(f"Integration bridge: added {root} to sys.path")
    return root


def try_import_existing_postgres_connection():
    """Optionally reuse the existing project's PG connection wrapper."""
    try:
        add_project_root_to_path()
        from database.connection import PostgresConnection as ExistingPC  # type: ignore
        logger.info("Integration bridge: using existing "
                    "database.connection.PostgresConnection")
        return ExistingPC
    except Exception as exc:
        logger.debug(f"Integration bridge: no existing PG wrapper ({exc})")
        return None
