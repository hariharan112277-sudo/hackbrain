"""
PostgreSQL repository for normalized telemetry.

Owns the ``iob_normalized_telemetry`` table schema and exposes a
simple ``save_telemetry()`` insert API used by the ingestion worker.

This module contains NO business-logic endpoints (those belong to
Member 1's REST API).  It only persists already-validated, already-
normalized UNS records.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

logger = logging.getLogger("iob.repository")


class TelemetryRepository:
    """Repository pattern over the ``iob_normalized_telemetry`` table."""

    # DDL is idempotent so re-running init is safe
    INIT_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS iob_normalized_telemetry (
            id              SERIAL PRIMARY KEY,
            device_id       VARCHAR(100) NOT NULL,
            site_id         VARCHAR(100) NOT NULL,
            area_id         VARCHAR(100) NOT NULL,
            timestamp_utc   TIMESTAMP WITH TIME ZONE NOT NULL,
            metrics         JSONB        NOT NULL,
            ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """
    INSERT_SQL = """
        INSERT INTO iob_normalized_telemetry
            (device_id, site_id, area_id, timestamp_utc, metrics)
        VALUES (%s, %s, %s, %s, %s);
    """

    def __init__(self, db_connection):
        self.conn = db_connection
        self._table_ready = False

    # ------------------------------------------------------------------
    def init_tables(self) -> None:
        """Idempotent schema bootstrap.  Call once at startup."""
        with self.conn.cursor() as cursor:
            cursor.execute(self.INIT_TABLE_SQL)
            self.conn.commit()
        self._table_ready = True
        logger.info("Telemetry table initialized (iob_normalized_telemetry)")

    # ------------------------------------------------------------------
    def save_telemetry(self, normalized_data: Dict[str, Any]) -> None:
        """
        Insert one normalized UNS record.

        ``normalized_data`` keys: ``device_id``, ``site_id``,
        ``area_id``, ``timestamp_utc``, ``metrics``.
        """
        if not self._table_ready:
            self.init_tables()
        with self.conn.cursor() as cursor:
            cursor.execute(
                self.INSERT_SQL,
                (
                    normalized_data["device_id"],
                    normalized_data["site_id"],
                    normalized_data["area_id"],
                    normalized_data["timestamp_utc"],
                    json.dumps(normalized_data["metrics"]),
                ),
            )
            self.conn.commit()
        logger.debug(
            f"Persisted telemetry: device={normalized_data['device_id']} "
            f"site={normalized_data['site_id']} area={normalized_data['area_id']}"
        )

    # ------------------------------------------------------------------
    def count_rows(self) -> int:
        """Convenience helper for smoke tests / status checks."""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM iob_normalized_telemetry;")
            row = cursor.fetchone()
        return int(row[0]) if row else 0

    def recent_rows(self, limit: int = 10) -> list:
        """Return the most recent N rows (debug / health-check helper)."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, device_id, site_id, area_id, timestamp_utc "
                "FROM iob_normalized_telemetry "
                "ORDER BY id DESC LIMIT %s;",
                (limit,),
            )
            return list(cursor.fetchall())
