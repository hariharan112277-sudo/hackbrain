#!/usr/bin/env python3
"""Export OpenAPI schema to static asset for immutability (Phase 6)."""
import json
from pathlib import Path

from app.main import app

output = Path("docs/openapi.json")
output.parent.mkdir(parents=True, exist_ok=True)
with output.open("w") as f:
    json.dump(app.openapi(), f, indent=2)
print(f"OpenAPI schema exported to {output}")
