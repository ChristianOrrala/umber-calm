"""Generated documentation (spec §11.3): the color-vision table, SVG renderings of the sample fixture, and the
README's swatches and badges."""
from __future__ import annotations

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from . import color, cvd, render_svg, safepath, sessions
from .palette import Palette

OWNER = "docs"
FIXTURE = "tests/fixtures/sample.spans.json"
VARIANTS = ("normal", "grayscale", "deuteranopia", "protanopia", "tritanopia")
BADGES = ("license", "release", "ports", "contrast")
BADGE_FONT = "ui-monospace, Menlo, Consolas, monospace"
BADGE_CHAR_W = 6.7  # 11px monospace advance; widths stay deterministic without measuring fonts
BADGE_PAD = 7


def _transform(kind: str):
    if kind == "normal":
        return lambda hx: hx
    return lambda hx: cvd.simulate(hx, kind)


def swatch(hx: str, outline: str) -> str:
    """A 20px rounded square; the outline keeps colors close to the page background visible."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">'
            f'<rect x="0.5" y="0.5" width="19" height="19" rx="4.5" fill="{hx}" stroke="{outline}"/></svg>\n')


def badge(label: str, value: str, pal: Palette) -> str:
    """A flat, neutral badge (no accent colors: accents carry meaning in this palette, never decoration)."""
    lw = round(BADGE_PAD * 2 + BADGE_CHAR_W * len(label), 1)
    vw = round(BADGE_PAD * 2 + BADGE_CHAR_W * len(value), 1)
    w = round(lw + vw, 1)
    text, label_bg, value_bg = pal.colors["text"], pal.colors["surface"], pal.colors["overlay"]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" viewBox="0 0 {w} 20" '
            f'font-family="{BADGE_FONT}" font-size="11">'
            f'<rect width="{w}" height="20" rx="4" fill="{label_bg}"/>'
            f'<rect x="{lw}" width="{vw}" height="20" rx="4" fill="{value_bg}"/>'
            f'<rect x="{lw}" width="4" height="20" fill="{value_bg}"/>'
            f'<text x="{BADGE_PAD}" y="14" fill="{text}">{escape(label)}</text>'
            f'<text x="{round(lw + BADGE_PAD, 1)}" y="14" fill="{text}">{escape(value)}</text></svg>\n')


def badge_values(pal: Palette, ports) -> dict[str, tuple[str, str]]:
    live = [p for p in ports if not p.archived_reason]
    ratio = color.contrast(pal.colors["text"], pal.colors["bg"])
    return {"license": ("license", pal.meta["license"]), "release": ("release", f"v{pal.meta['release']}"),
            "ports": ("ports", str(len(live))), "contrast": ("text contrast", f"{ratio:.1f}:1")}


STRIP = ("grayscale", "deuteranopia", "protanopia", "tritanopia")
STRIP_WIDTH, STRIP_GAP = 760, 12  # the README's image width, so the strip lines up with the renders above it


def strip(renders: dict[str, str], pal: Palette) -> str:
    """The four simulated renders in one image: each render nested at thumbnail size, labeled in normal colors."""
    first = renders[STRIP[0]]
    head = re.match(r'<svg [^>]*viewBox="0 0 ([\d.]+) ([\d.]+)"[^>]*>', first)
    rw, rh = float(head.group(1)), float(head.group(2))
    tw = (STRIP_WIDTH - STRIP_GAP * (len(STRIP) - 1)) / len(STRIP)
    th = round(rh * tw / rw, 1)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{STRIP_WIDTH}" height="{th}" viewBox="0 0 {STRIP_WIDTH} {th}">']
    for i, kind in enumerate(STRIP):
        x = round(i * (tw + STRIP_GAP), 1)
        body = renders[kind]
        opening = re.match(r"<svg [^>]*>", body).group(0)
        nested = opening.replace('xmlns="http://www.w3.org/2000/svg" ', "")
        nested = re.sub(r' width="[\d.]+" height="[\d.]+"', f' x="{x}" y="0" width="{round(tw, 1)}" height="{th}"', nested, count=1)
        out.append(nested + body[len(opening):].strip())
        label = kind.capitalize()
        lw = round(10 * 0.6 * len(label) + 10, 1)  # 10px monospace label plus padding
        lx = round(x + tw - 6 - lw, 1)
        out.append(f'<rect x="{lx}" y="6" width="{lw}" height="16" rx="4" fill="{pal.colors["bg"]}"/>')
        out.append(f'<text x="{round(lx + 5, 1)}" y="18" font-family="{BADGE_FONT}" font-size="10" '
                   f'fill="{pal.colors["text"]}">{label}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def plan(root: Path, pal: Palette, ports=()) -> dict[str, tuple[str, bytes]]:
    """Planned docs under the owner "docs". Empty in repositories without the fixture (test fixtures)."""
    path = safepath.inside(root, FIXTURE)
    if not path.is_file():
        return {}
    fixture = json.loads(path.read_text(encoding="utf-8"))
    out = {"docs/color-vision.md": (OWNER, cvd.report(pal).encode("utf-8"))}
    renders = {kind: render_svg.render(fixture, pal, _transform(kind)) for kind in VARIANTS}
    for kind, svg in renders.items():
        out[f"docs/renders/{kind}.svg"] = (OWNER, svg.encode("utf-8"))
    out["docs/renders/color-vision.svg"] = (OWNER, strip(renders, pal).encode("utf-8"))
    for name in sessions.NAMES:
        out[f"docs/renders/session-{name}.svg"] = (OWNER, sessions.render(name, pal).encode("utf-8"))
    outline = pal.resolve("ui.text_dim")
    for name, hx in pal.colors.items():
        out[f"docs/swatches/{name}.svg"] = (OWNER, swatch(hx, outline).encode("utf-8"))
    for name, (label, value) in badge_values(pal, ports).items():
        out[f"docs/badges/{name}.svg"] = (OWNER, badge(label, value, pal).encode("utf-8"))
    return out
