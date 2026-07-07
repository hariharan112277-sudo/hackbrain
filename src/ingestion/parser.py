"""
Normalization engine.

Converts a *validated* ``TelemetryPayloadSchema`` plus the originating
MQTT topic into the canonical Unified-Namespace (UNS) record that is
persisted to PostgreSQL::

    {
      "device_id":      "<id>",
      "site_id":        "<site>",        # extracted from topic
      "area_id":        "<area>",        # extracted from topic
      "timestamp_utc":  "<ISO-8601 UTC>",
      "metrics":        {metric_name: value, ...}
    }

Topic convention (matches ``simulator_config.yaml``)::

    iob/uns/<site>/<area>/<device_id>/telemetry
"""
from __future__ import annotations

import datetime
import logging
from typing import Any, Dict

from .validator import TelemetryPayloadSchema

logger = logging.getLogger("iob.parser")


class NormalizationEngine:
    """Stateless UNS-aware normalization engine."""

    @staticmethod
    def normalize(
        parsed_data: TelemetryPayloadSchema,
        topic: str,
    ) -> Dict[str, Any]:
        """
        Build the canonical UNS record from a validated payload + topic.

        - Converts epoch float timestamp to ISO 8601 UTC string.
        - Splits ``site_id`` and ``area_id`` out of the UNS topic path.
        """
        utc_dt = datetime.datetime.fromtimestamp(
            parsed_data.timestamp, tz=datetime.timezone.utc,
        )

        topic_parts = topic.split("/")
        # Expected: iob / uns / <site> / <area> / <device> / telemetry
        site = topic_parts[2] if len(topic_parts) > 2 else "unknown_site"
        area = topic_parts[3] if len(topic_parts) > 3 else "unknown_area"

        record = {
            "device_id":     parsed_data.device_id,
            "site_id":       site,
            "area_id":       area,
            "timestamp_utc": utc_dt.isoformat(),
            "metrics":       dict(parsed_data.telemetry),
        }
        return record

    @staticmethod
    def parse_topic(topic: str) -> Dict[str, str]:
        """
        Extract UNS components from a topic path.  Returns a dict with
        keys ``site_id``, ``area_id``, ``device_id``, ``leaf``.
        Missing components default to ``"unknown_<name>"``.
        """
        parts = topic.split("/")
        return {
            "site_id":   parts[2] if len(parts) > 2 else "unknown_site",
            "area_id":   parts[3] if len(parts) > 3 else "unknown_area",
            "device_id": parts[4] if len(parts) > 4 else "unknown_device",
            "leaf":      parts[5] if len(parts) > 5 else "",
        }
