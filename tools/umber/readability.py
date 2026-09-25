"""Measured foreground/background pairs (spec §4.2 and §4.4) and their minimum contrast."""
from __future__ import annotations

from . import color
from .palette import ANSI_SLOTS, Palette

ACCENTS = ("yellow", "blue", "cyan", "green", "purple", "subtle")
DIFF_KINDS = ("add", "delete", "change")

PAIRS: list[tuple[str, str, str, float]] = [
    ("text on bg", "text", "bg", 4.5),
    ("text on surface", "text", "surface", 4.5),
    *[(f"{a} on bg", a, "bg", 4.5) for a in ACCENTS],
    *[(f"{a} on surface", a, "surface", 4.5) for a in ACCENTS],
    ("red on bg", "red", "bg", 4.5),
    ("red on surface", "red", "surface", 4.5),
    ("muted on bg", "muted", "bg", 4.5),
    ("muted on surface (E1)", "muted", "surface", 4.0),
    ("dim_text on bg (E2)", "dim_text", "bg", 3.0),
    ("orange on bg", "orange", "bg", 3.0),
    ("orange on surface", "orange", "surface", 3.0),
    ("text on selection", "text", "overlay", 4.5),
    ("muted on selection (E3)", "muted", "overlay", 3.0),
    ("text on search match", "text", "blend:diag.search:bg:tint.search", 4.5),
    ("muted on search match (E3)", "muted", "blend:diag.search:bg:tint.search", 3.0),
    ("bg on current search match", "bg", "diag.search", 4.5),
    ("cursor text on cursor", "term.cursor_text", "term.cursor", 4.5),
    *[(f"text on diff {k}", "text", f"blend:diag.diff_{k}:bg:tint.diff", 4.5) for k in DIFF_KINDS],
    *[(f"muted on diff {k} (E3)", "muted", f"blend:diag.diff_{k}:bg:tint.diff", 3.0) for k in DIFF_KINDS],
    *[(f"text on light diff {k}", "text", f"blend:diag.diff_{k}:bg:tint.diag", 4.5) for k in DIFF_KINDS],
    *[(f"muted on light diff {k} (E3)", "muted", f"blend:diag.diff_{k}:bg:tint.diag", 3.0) for k in DIFF_KINDS],
    *[(f"{s} virtual text", f"diag.{s}", f"blend:diag.{s}:bg:tint.diag", 4.5) for s in ("error", "warning", "info", "hint")],
    ("ansi.bright_black on bg (E2)", "ansi.bright_black", "bg", 3.0),
    *[(f"ansi.{s} on bg", f"ansi.{s}", "bg", 4.5) for s in ANSI_SLOTS if s not in ("black", "bright_black")],
]


def _background(pal: Palette, spec: str) -> str:
    if spec.startswith("blend:"):
        _, fg, base, amount = spec.split(":")
        return color.blend(pal.resolve(fg), pal.resolve(base), pal.tint(amount))
    return pal.resolve(spec)


def measured_blends(pal: Palette) -> set[str]:
    """Every blended background that §4.4 measures. Templates may only blend to one of these (the closed set)."""
    return {_background(pal, bg) for _, _, bg, _ in PAIRS if bg.startswith("blend:")}


def problems(pal: Palette) -> list[str]:
    found = []
    for label, fg, bg, minimum in PAIRS:
        ratio = color.contrast(pal.resolve(fg), _background(pal, bg))
        if ratio < minimum:
            found.append(f"readability: {label} is {ratio:.2f}:1, below {minimum}:1")
    return found
