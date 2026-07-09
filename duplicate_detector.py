"""
Sliding Window Duplicate Detector Stage for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: IEC 62443 Replay Attack Mitigation, High-Throughput Edge Deduplication.
Section 4 Implementation.
"""

import threading
import time
import logging
from typing import Dict, Any, Set, Tuple
from .exceptions import DuplicatePacketException

logger = logging.getLogger("iob.dedup")


class SlidingWindowDuplicateDetector:
    """Thread-safe sliding cache window filter to intercept duplicate MQTT messages."""
    def __init__(self, window_sec: float = 60.0, max_elements: int = 50000, window_seconds: float = None):
        self.window = window_seconds if window_seconds is not None else window_sec
        self.max_elements = max_elements
        self.lock = threading.Lock()

        # In-memory deduplication set cache store with timestamps
        self.fingerprint_registry: Dict[Tuple[str, int], float] = {}

    def process_deduplication_check(self, payload: Dict[str, Any]) -> bool:
        sensor_id = payload.get("sensor_id", payload.get("message_id", ""))
        seq_num = payload.get("sequence_number", -1)

        fingerprint = (str(sensor_id), int(seq_num))
        now = time.time()

        with self.lock:
            # Purge expired entries inside sliding window
            expired = [fp for fp, ts in self.fingerprint_registry.items() if (now - ts) > self.window]
            for fp in expired:
                del self.fingerprint_registry[fp]

            if fingerprint in self.fingerprint_registry:
                return True

            if len(self.fingerprint_registry) >= self.max_elements:
                self.fingerprint_registry.clear()
                logger.warning("Deduplication register limit reached. Cleared cache.")

            self.fingerprint_registry[fingerprint] = now
            return False

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.process_deduplication_check(payload):
            raise DuplicatePacketException(f"Duplicate sequence discarded: {payload.get('sensor_id')} #{payload.get('sequence_number')}")
        return payload
