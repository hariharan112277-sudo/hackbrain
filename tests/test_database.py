"""Tests for the PostgreSQL repository (mocked DB connection)."""
import unittest
from unittest.mock import MagicMock

from src.database.telemetry_repository import TelemetryRepository


class TestTelemetryRepository(unittest.TestCase):
    def _make_conn(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (42,)
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cursor
        return conn, cursor

    def test_init_tables_creates_table(self):
        conn, cursor = self._make_conn()
        repo = TelemetryRepository(conn)
        repo.init_tables()
        # First execute() call should be the CREATE TABLE
        sql = cursor.execute.call_args_list[0].args[0]
        self.assertIn("CREATE TABLE IF NOT EXISTS iob_normalized_telemetry", sql)
        # Strip whitespace before substring check (SQL is pretty-printed)
        self.assertIn("SERIAL PRIMARY KEY", sql.replace("  ", " "))
        self.assertIn("JSONB", sql)
        conn.commit.assert_called()

    def test_save_telemetry_inserts_row(self):
        conn, cursor = self._make_conn()
        repo = TelemetryRepository(conn)
        repo.init_tables()

        normalized = {
            "device_id": "DEV_CNC_001",
            "site_id": "site_alpha",
            "area_id": "area_machining",
            "timestamp_utc": "2024-01-01T00:00:00+00:00",
            "metrics": {"spindle_speed_rpm": 8500.0,
                        "vibration_amplitude_g": 1.2},
        }
        repo.save_telemetry(normalized)

        # Find the INSERT call (last one)
        insert_call = None
        for call in cursor.execute.call_args_list:
            sql = call.args[0]
            if "INSERT INTO" in sql:
                insert_call = call
                break
        self.assertIsNotNone(insert_call)
        params = insert_call.args[1]
        self.assertEqual(params[0], "DEV_CNC_001")
        self.assertEqual(params[1], "site_alpha")
        self.assertEqual(params[2], "area_machining")
        self.assertEqual(params[3], "2024-01-01T00:00:00+00:00")
        # metrics serialized to JSON
        import json
        self.assertEqual(json.loads(params[4]), normalized["metrics"])

    def test_save_telemetry_auto_inits_table(self):
        """First save should auto-call init_tables() if not already done."""
        conn, cursor = self._make_conn()
        repo = TelemetryRepository(conn)
        # Don't call init_tables() manually
        repo.save_telemetry({
            "device_id": "X", "site_id": "S", "area_id": "A",
            "timestamp_utc": "2024-01-01T00:00:00+00:00",
            "metrics": {"m": 1.0},
        })
        # Should have seen CREATE then INSERT
        sqls = [c.args[0] for c in cursor.execute.call_args_list]
        self.assertTrue(any("CREATE TABLE" in s for s in sqls))
        self.assertTrue(any("INSERT INTO" in s for s in sqls))


if __name__ == "__main__":
    unittest.main()
