"""Deterministic SVG rendering of the design fixture (spec §11.3). Standard library only."""
from __future__ import annotations

from typing import Callable
from xml.sax.saxutils import escape

from . import color

CHAR_W = 8.4
LINE_H = 20
PAD = 16
FONT_SIZE = 14
CORNER = 10  # rounded background: a card on GitHub's light page; on the dark page the edge stays soft (1.15:1)
LINE_STATES = ("diff_add", "diff_delete", "diff_change")
SPAN_STATES = ("selection", "search", "search_current")
SEVERITIES = ("error", "warning", "info", "hint")


def _num(x: float) -> str:
    return f"{x:.1f}"


class _Colors:
    def __init__(self, pal, transform: Callable[[str], str]):
        self.pal, self.transform = pal, transform

    def ref(self, ref: str) -> str:
        return self.transform(self.pal.resolve(ref))

    def tint(self, ref: str, tint: str) -> str:
        return self.transform(color.blend(self.pal.resolve(ref), self.pal.resolve("bg"), self.pal.tint(tint)))


def _span_state(c: _Colors, state: str) -> tuple[str, str]:
    """(background, foreground) forced by a span state; matches the Neovim/Vim groups."""
    if state == "selection":
        return c.ref("ui.selection_bg"), c.ref("ui.selection_fg")
    if state == "search":
        return c.tint("diag.search", "tint.search"), c.ref("ui.text")
    if state == "search_current":
        return c.ref("diag.search"), c.ref("ui.bg")
    raise ValueError(f"unknown span state {state!r}")


def render(fixture: dict, pal, transform: Callable[[str], str] = lambda hx: hx) -> str:
    c = _Colors(pal, transform)
    rows: list[tuple[str, dict | None]] = []
    for f in fixture["files"]:
        rows.append(("header", {"text": f["name"]}))
        rows += [("code", line) for line in f["lines"]]
        rows.append(("blank", None))
    rows.pop()
    widths = []
    for kind, line in rows:
        if kind == "code":
            n = sum(len(s[1]) for s in line["spans"])
            if "diagnostic" in line:
                n += 4 + len(line["diagnostic"]["text"])
            widths.append(n)
        elif kind == "header":
            widths.append(len(line["text"]))
    width = PAD * 2 + CHAR_W * max(widths)
    height = PAD * 2 + LINE_H * len(rows)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{_num(width)}" height="{_num(height)}" '
           f'viewBox="0 0 {_num(width)} {_num(height)}" font-family="ui-monospace, Menlo, Consolas, monospace" '
           f'font-size="{FONT_SIZE}">',
           f'<rect width="{_num(width)}" height="{_num(height)}" rx="{CORNER}" fill="{c.ref("ui.bg")}"/>']
    for i, (kind, line) in enumerate(rows):
        top = PAD + LINE_H * i
        base = top + LINE_H - 6
        if kind == "header":
            out.append(f'<text x="{_num(PAD)}" y="{_num(base)}" fill="{c.ref("ui.text_secondary")}">'
                       f'{escape(line["text"])}</text>')
            continue
        if kind == "blank":
            continue
        state = line.get("state")
        if state:
            if state not in LINE_STATES:
                raise ValueError(f"unknown line state {state!r}")
            out.append(f'<rect x="0" y="{_num(top)}" width="{_num(width)}" height="{LINE_H}" '
                       f'fill="{c.tint("diag." + state, "tint.diff")}"/>')
        col, tspans = 0, []
        for span in line["spans"]:
            role, text = span[0], span[1]
            fill = c.ref("syntax." + role) if role else c.ref("ui.text")
            if len(span) > 2:
                bg, fill = _span_state(c, span[2])
                out.append(f'<rect x="{_num(PAD + CHAR_W * col)}" y="{_num(top)}" width="{_num(CHAR_W * len(text))}" '
                           f'height="{LINE_H}" fill="{bg}"/>')
            tspans.append(f'<tspan x="{_num(PAD + CHAR_W * col)}" fill="{fill}">{escape(text)}</tspan>')
            col += len(text)
        diag = line.get("diagnostic")
        if diag:
            sev = diag["severity"]
            if sev not in SEVERITIES:
                raise ValueError(f"unknown severity {sev!r}")
            text = "● " + diag["text"]
            x = PAD + CHAR_W * (col + 2)
            out.append(f'<rect x="{_num(x)}" y="{_num(top)}" width="{_num(CHAR_W * len(text))}" height="{LINE_H}" '
                       f'fill="{c.tint("diag." + sev, "tint.diag")}"/>')
            tspans.append(f'<tspan x="{_num(x)}" fill="{c.ref("diag." + sev)}">{escape(text)}</tspan>')
        out.append(f'<text y="{_num(base)}" xml:space="preserve">{"".join(tspans)}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"
