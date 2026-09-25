"""Generated documentation (spec §11.3): the color-vision table and SVG renderings of the sample fixture."""
from __future__ import annotations

import json
from pathlib import Path

from . import cvd, render_svg, safepath
from .palette import Palette

OWNER = "docs"
FIXTURE = "tests/fixtures/sample.spans.json"
VARIANTS = ("normal", "grayscale", "deuteranopia", "protanopia", "tritanopia")


def _transform(kind: str):
    if kind == "normal":
        return lambda hx: hx
    return lambda hx: cvd.simulate(hx, kind)


def plan(root: Path, pal: Palette) -> dict[str, tuple[str, bytes]]:
    """Planned docs under the owner "docs". Empty in repositories without the fixture (test fixtures)."""
    path = safepath.inside(root, FIXTURE)
    if not path.is_file():
        return {}
    fixture = json.loads(path.read_text(encoding="utf-8"))
    out = {"docs/color-vision.md": (OWNER, cvd.report(pal).encode("utf-8"))}
    for kind in VARIANTS:
        out[f"docs/renders/{kind}.svg"] = (OWNER, render_svg.render(fixture, pal, _transform(kind)).encode("utf-8"))
    return out
