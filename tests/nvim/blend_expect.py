"""Print, as JSON, the tints the Python generator computes; tests/nvim/run.lua compares them with Lua."""
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from umber import color, palette  # noqa: E402

pal = palette.load(ROOT / "palette" / "umber-calm.toml")
bg = pal.colors["bg"]
amount = {"search": "search", "diff_add": "diff", "diff_delete": "diff", "diff_change": "diff",
          "error": "diag", "warning": "diag", "info": "diag", "hint": "diag"}
out = {role: color.blend(pal.resolve(f"diag.{role}"), bg, pal.tints[tint]) for role, tint in amount.items()}
out["boundary"] = color.blend("#000000", "#050505", Fraction(9, 10))
print(json.dumps(out, sort_keys=True))
