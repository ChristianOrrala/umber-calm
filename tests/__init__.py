"""Test package. Importing it puts tools/ on sys.path, so every test module runs standalone."""
import sys
from pathlib import Path

_TOOLS = str(Path(__file__).resolve().parents[1] / "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
