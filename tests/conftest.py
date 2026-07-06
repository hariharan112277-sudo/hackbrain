"""
Pytest bootstrap: make the flat ``simulator/`` modules importable as top-level
modules (``from generator import ...``) without installing the package.
"""

import sys
from pathlib import Path

SIMULATOR_DIR = str(Path(__file__).resolve().parent.parent / "simulator")
if SIMULATOR_DIR not in sys.path:
    sys.path.insert(0, SIMULATOR_DIR)
