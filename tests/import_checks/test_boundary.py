"""Import Boundary Enforcement Tests — Phase 0 Remediation.
Ensures Track B modules do not directly import Track A database modules.
"""
import ast
import sys
from pathlib import Path

def test_no_direct_import_from_realtime_ai_db():
    """Verify deprecated db.py is not imported by streaming workers."""
    workers_path = Path("app/realtime_ai/streaming/workers.py")
    content = workers_path.read_text()
    assert "from app.realtime_ai.utils.db import" not in content
    assert "app.realtime_ai.utils.db_async" in content
