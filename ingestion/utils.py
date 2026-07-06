"""
Utility helpers for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: Payload hashing, ISA-95 hierarchy extraction, DLQ persistence.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def compute_payload_fingerprint(data: Any) -> str:
    """Computes a SHA-256 deterministic hash fingerprint for deduplication or auditing."""
    if isinstance(data, dict):
        serialized = json.dumps(data, sort_keys=True).encode("utf-8")
    elif isinstance(data, str):
        serialized = data.encode("utf-8")
    elif isinstance(data, bytes):
        serialized = data
    else:
        serialized = str(data).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def parse_isa95_topic(topic: str, delimiter: str = "/") -> Dict[str, str]:
    """
    Parses hierarchical MQTT topic into ISA-95 structural components.
    Example: 'site1/area1/line1/turbine-01/telemetry' -> site, area, line, equipment
    """
    parts = [p for p in topic.split(delimiter) if p]
    if len(parts) >= 4:
        return {
            "enterprise": "IOB_ENTERPRISE",
            "site": parts[0],
            "area": parts[1],
            "line": parts[2],
            "equipment": parts[3],
        }
    elif len(parts) > 0:
        return {
            "enterprise": "IOB_ENTERPRISE",
            "site": "SITE_DEFAULT",
            "area": "AREA_DEFAULT",
            "line": "LINE_DEFAULT",
            "equipment": parts[-1],
        }
    return {
        "enterprise": "IOB_ENTERPRISE",
        "site": "SITE_DEFAULT",
        "area": "AREA_DEFAULT",
        "line": "LINE_DEFAULT",
        "equipment": "UNKNOWN",
    }


class DeadLetterQueueRecorder:
    """Records failed or unparseable telemetry packets to disk or memory for manual review and re-ingestion."""

    def __init__(self, dlq_dir: Optional[str] = None):
        self.memory_dlq: List[Dict[str, Any]] = []
        if dlq_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            dlq_dir = os.path.join(base_dir, "dlq")
        self.dlq_dir = dlq_dir

    def record_failure(self, raw_packet: Any, error: Exception) -> None:
        entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "stage": getattr(error, "stage", "Unknown"),
            "raw_packet": str(raw_packet),
        }
        self.memory_dlq.append(entry)

        try:
            os.makedirs(self.dlq_dir, exist_ok=True)
            filename = f"dlq_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}.json"
            filepath = os.path.join(self.dlq_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2)
        except Exception:
            # Fallback if disk is read-only
            pass
