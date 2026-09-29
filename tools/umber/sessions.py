"""Calm session renders for the README (standard library only): a Claude Code session with its diff panel,
an editor and a terminal. Every color is a palette role; amber marks only where you are, red only a deletion."""
from __future__ import annotations

from xml.sax.saxutils import escape

MONO = "ui-monospace, Menlo, Consolas, monospace"
ADVANCE = 0.6  # monospace advance per em: character columns line up at any font size
CORNER = 12
NAMES = ("claude", "editor", "terminal")
STEEP = "4"


def _num(x: float) -> str:
    return f"{x:.1f}"


class _Canvas:
    """SVG builder that records every (foreground, background) role pair it draws, so tests measure what is drawn."""

    def __init__(self, pal, width: float, height: float, size: float):
        self.pal, self.w, self.h, self.size = pal, width, height, size
        self.text_pairs: set[tuple[str, str]] = set()
        self.mark_pairs: set[tuple[str, str]] = set()  # non-text marks that carry meaning (a status dot)
        self.out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{_num(width)}" height="{_num(height)}" '
                    f'viewBox="0 0 {_num(width)} {_num(height)}" font-family="{MONO}" font-size="{size}">',
                    f'<clipPath id="card"><rect width="{_num(width)}" height="{_num(height)}" rx="{CORNER}"/></clipPath>',
                    '<g clip-path="url(#card)">']

    def c(self, ref: str) -> str:
        return self.pal.resolve(ref)

    def rect(self, x, y, w, h, ref: str, rx: float = 0, stroke: str = "") -> None:
        extra = (f' rx="{rx}"' if rx else "") + (f' stroke="{self.c(stroke)}"' if stroke else "")
        self.out.append(f'<rect x="{_num(x)}" y="{_num(y)}" width="{_num(w)}" height="{_num(h)}"{extra} fill="{self.c(ref)}"/>')

    def dot(self, cx, cy, r, ref: str, on: str) -> None:
        self.mark_pairs.add((ref, on))
        self.out.append(f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{r}" fill="{self.c(ref)}"/>')

    def text(self, x, y, parts, on: str, size: float | None = None, anchor: str = "") -> float:
        """One line of (role, text) or (role, text, "bold") parts drawn on the `on` role; returns its width."""
        size = size or self.size
        cw = size * ADVANCE
        if anchor == "end":
            x -= cw * sum(len(p[1]) for p in parts)
        col, spans = 0, []
        for part in parts:
            ref, txt = part[0], part[1]
            if txt.strip():
                self.text_pairs.add((ref, on))
            bold = ' font-weight="600"' if len(part) > 2 else ""
            spans.append(f'<tspan x="{_num(x + cw * col)}" fill="{self.c(ref)}"{bold}>{escape(txt)}</tspan>')
            col += len(txt)
        fs = f' font-size="{size}"' if size != self.size else ""
        self.out.append(f'<text y="{_num(y)}"{fs} xml:space="preserve">{"".join(spans)}</text>')
        return cw * col

    def svg(self) -> str:
        return "\n".join(self.out + ["</g>", "</svg>"]) + "\n"


def _brew_code() -> list[list[tuple]]:
    k, ns, fn, ty, co, st, op, esc = ("syntax.keyword", "syntax.namespace", "syntax.function", "syntax.type",
                                      "syntax.constant", "syntax.string", "syntax.operator", "syntax.escape")
    v, t, b = "syntax.variable", "ui.text", "syntax.builtin"
    return [
        [("syntax.comment", "# A slow afternoon: steep, wait, pour.")],
        [(k, "from"), (t, " "), (ns, "time"), (t, " "), (k, "import"), (t, " "), (fn, "sleep")],
        [],
        [(co, "STEEP_MINUTES"), (t, " "), (op, "="), (t, " "), (co, STEEP)],
        [],
        [(k, "def"), (t, " "), (fn, "brew"), (op, "("), (v, "tea"), (op, ":"), (t, " "), (ty, "str"), (op, ","), (t, " "),
         (v, "cups"), (op, ":"), (t, " "), (ty, "int"), (t, " "), (op, "="), (t, " "), (co, "1"), (op, ")"), (t, " "),
         (op, "->"), (t, " "), (ty, "str"), (op, ":")],
        [(t, "    "), (st, '"""Steep the leaves, then pour."""')],
        [(t, "    "), (fn, "sleep"), (op, "("), (co, "STEEP_MINUTES"), (t, " "), (op, "*"), (t, " "), (co, "60"), (op, ")")],
        [(t, "    "), (k, "return"), (t, " "), (st, 'f"'), (esc, "{"), (v, "cups"), (esc, "}"), (st, " cups of "),
         (esc, "{"), (v, "tea"), (esc, "}"), (st, ', ready"')],
        [],
        [(b, "print"), (op, "("), (fn, "brew"), (op, "("), (st, '"genmaicha"'), (op, ","), (t, " "), (v, "cups"),
         (op, "="), (co, "2"), (op, "))")],
    ]


def _claude(pal) -> _Canvas:
    """Transcript on the background (the port's userMessageBackground), the diff panel on the surface
    (composerSidebarBackground), counts and markers in ANSI bright green and red as the app draws them."""
    w, h, split, size = 760, 552, 360, 13  # the full render's proportions; the extra height stays empty on purpose
    cv = _Canvas(pal, w, h, size)
    cw = size * ADVANCE
    panel_h = h - 108
    add, rem, bg, panel = "ansi.bright_green", "ansi.bright_red", "ui.bg", "ui.surface"
    cv.rect(0, 0, w, h, bg)
    cv.rect(split, 0, w - split, panel_h, panel)
    x = 16
    cv.text(x, 32, [("diag.ok", "❯ "), ("ui.text", "read the steep time from settings")], bg)
    cv.text(x, 64, [("ui.text", "● I'll read it from the settings file")], bg)
    cv.text(x + cw * 2, 82, [("ui.text", "and keep 4 minutes as the default.")], bg)
    cv.text(x, 114, [("diag.ok", "● "), ("ui.text", "Update", "bold"), ("ui.text_secondary", "("),
                     ("syntax.link", "brew.py"), ("ui.text_secondary", ")")], bg)
    cv.text(x + cw * 2, 132, [("ui.text_secondary", "⎿ Added 2 lines, removed 1 line")], bg)
    full = w - 2 * x
    cv.rect(x, h - 92, full, 1, "ui.border_strong")
    cv.text(x, h - 66, [("diag.ok", "❯")], bg)
    cv.rect(x + cw * 2, h - 80, cw, 18, "ui.focus")  # the cursor: focus
    cv.rect(x, h - 52, full, 1, "ui.border_strong")
    mode, small = "accept edits", 12.5
    chip = small * ADVANCE * len(mode) + 16
    sy = h - 36
    cv.rect(x, sy, chip, 20, "ui.focus", rx=5)  # the active mode: focus
    cv.text(x + 8, sy + 14.5, [("ui.bg", mode, "bold")], "ui.focus", size=small)
    cv.text(x + chip + 14, sy + 14.5, [("syntax.constant", "main"), ("ui.text_secondary", "  ·  "), ("ui.text", "brew.py"),
                                       ("ui.text_secondary", "  ·  "), (add, "+2"), ("ui.text_secondary", " "),
                                       (rem, "-1")], bg, size=small)
    cv.text(w - x, sy + 14.5, [("ui.text_secondary", "16:20")], bg, size=small, anchor="end")
    px, rule_w = split + 18, w - split - 36
    cv.text(px, 30, [("ui.text", "1 file changed", "bold"), ("ui.text", " "), (add, "+2"), ("ui.text", " "), (rem, "-1")], panel)
    cv.text(px, 56, [("ui.text", "brew.py")], panel)
    cv.text(w - 18, 56, [(add, "+2"), ("ui.text", " "), (rem, "-1")], panel, anchor="end")
    cv.rect(px, 68, rule_w, 1, "ui.border_strong")
    cv.text(px, 90, [("ui.text", "brew.py", "bold")], panel)
    cv.rect(px, 100, rule_w, 1, "ui.border_strong")
    k, ns, fn, co, st, op, t = ("syntax.keyword", "syntax.namespace", "syntax.function", "syntax.constant",
                                "syntax.string", "syntax.operator", "ui.text")
    rows = [(" 2", " ", [(k, "from"), (t, " "), (ns, "time"), (t, " "), (k, "import"), (t, " "), (fn, "sleep")], "ui.text_secondary"),
            (" 3", "+", [(k, "from"), (t, " "), (ns, "settings"), (t, " "), (k, "import"), (t, " "), (fn, "get")], add),
            (" 4", " ", [], "ui.text_secondary"),
            (" 5", "-", [("ui.text_secondary", f"STEEP_MINUTES = {STEEP}")], rem),  # a deletion: the only red
            (" 5", "+", [(co, "STEEP_MINUTES"), (t, " "), (op, "="), (t, " "), (fn, "get"), (op, "("), (st, '"steep"'),
                         (op, ","), (t, " "), (co, STEEP), (op, ")")], add)]
    for i, (num, mark, parts, gutter) in enumerate(rows):
        y = 122 + 20 * i
        cv.text(px, y, [(gutter, num), (gutter, " " + mark)], panel)
        if parts:
            cv.text(px + cw * 5, y, parts, panel)
    return cv


def _editor(pal) -> _Canvas:
    code = _brew_code()
    w, tab_h, status_h, size = 760, 34, 26, 14
    cw, lh = size * ADVANCE, 20
    top = tab_h + 14
    h = top + lh * len(code) + 18 + status_h
    cv = _Canvas(pal, w, h, size)
    gutter = 4 * cw + 16
    cur_line, cur_col = len(code) - 1, sum(len(p[1]) for p in code[-1])
    cv.rect(0, 0, w, h, "ui.bg")
    cv.rect(0, 0, w, tab_h, "ui.chrome")
    cv.rect(0, 0, 132, tab_h, "ui.bg")
    cv.rect(0, 0, 132, 2, "ui.focus")  # the active tab: focus
    cv.text(16, 22, [("ui.text", "brew.py")], "ui.bg")
    cv.text(148, 22, [("ui.text_secondary", "notes.md")], "ui.chrome")
    cv.rect(0, top + lh * cur_line, w, lh, "ui.surface")  # the current line
    for i, parts in enumerate(code):
        base = top + lh * i + lh - 6
        on = "ui.surface" if i == cur_line else "ui.bg"
        number = str(i + 1)
        ref = "ui.line_number_active" if i == cur_line else "ui.line_number"
        cv.text(gutter - 12 - cw * len(number), base, [(ref, number)], on)
        if parts:
            cv.text(gutter, base, parts, on)
    cv.rect(gutter + cw * cur_col, top + lh * cur_line + 2, cw, lh - 4, "ui.focus")  # the cursor: focus
    nw, nh = 196, 30
    nx, ny = w - nw - 14, tab_h + 12
    cv.rect(nx, ny, nw, nh, "ui.surface", rx=7, stroke="ui.border_strong")
    cv.dot(nx + 15, ny + nh / 2, 3.5, "diag.info", "ui.surface")
    cv.text(nx + 27, ny + 20, [("ui.text", "Saved brew.py")], "ui.surface", size=12.5)
    cv.text(nx + nw - 12, ny + 20, [("ui.text_secondary", "now")], "ui.surface", size=12, anchor="end")
    sy, mode = h - status_h, "NORMAL"
    mode_w = 13 * ADVANCE * len(mode) + 20
    cv.rect(0, sy, w, status_h, "ui.surface")
    cv.rect(0, sy, mode_w, status_h, "ui.focus")  # the active mode: focus
    cv.text(10, sy + 18, [("ui.bg", mode, "bold")], "ui.focus", size=13)
    cv.text(mode_w + 14, sy + 18, [("ui.text_secondary", "main"), ("ui.text", "   brew.py")], "ui.surface", size=13)
    cv.text(w - 14, sy + 18, [("ui.text_secondary", "python   utf-8   11:34")], "ui.surface", size=13, anchor="end")
    return cv


def _terminal(pal) -> _Canvas:
    w, status_h, size, lh, pad = 760, 26, 14, 20, 16
    lines = [
        [("ui.text", "~/tea", "bold"), ("ui.text_secondary", " on "), ("syntax.constant", "main")],
        [("diag.ok", "❯ "), ("ui.text", "python brew.py")],
        [("ui.text", "2 cups of genmaicha, ready")],
        [],
        [("ui.text", "~/tea", "bold"), ("ui.text_secondary", " on "), ("syntax.constant", "main"),
         ("ui.text_secondary", " took 4m0s")],
        [("diag.ok", "❯ ")],
    ]
    h = pad + lh * len(lines) + 34 + status_h
    cv = _Canvas(pal, w, h, size)
    cw = size * ADVANCE
    cv.rect(0, 0, w, h, "ui.bg")
    for i, parts in enumerate(lines):
        base = pad + 8 + lh * i + lh - 6
        width = cv.text(pad, base, parts, "ui.bg") if parts else 0
        if i == len(lines) - 1:
            cv.rect(pad + width, pad + 8 + lh * i + 2, cw, lh - 4, "ui.focus")  # the cursor: focus
    nw, nh = 214, 30
    nx, ny = w - nw - 14, 14
    cv.rect(nx, ny, nw, nh, "ui.surface", rx=7, stroke="ui.border_strong")
    cv.dot(nx + 15, ny + nh / 2, 3.5, "diag.info", "ui.surface")
    cv.text(nx + 27, ny + 20, [("ui.text", "Timer done: 4 min")], "ui.surface", size=12.5)
    cv.text(nx + nw - 12, ny + 20, [("ui.text_secondary", "now")], "ui.surface", size=12, anchor="end")
    sy = h - status_h
    cv.rect(0, sy, w, status_h, "ui.surface")
    cv.text(12, sy + 18, [("ui.text", "[tea] "), ("ui.text", " "), ("ui.focus", "1:brew*", "bold"),  # current window: focus
                          ("ui.text", "  "), ("ui.text_secondary", "2:notes")], "ui.surface", size=13)
    cv.text(w - 12, sy + 18, [("ui.text_secondary", "16:20")], "ui.surface", size=13, anchor="end")
    return cv


_DRAW = {"claude": _claude, "editor": _editor, "terminal": _terminal}
PANELS = ("ui.surface", "ui.chrome")


def render(name: str, pal) -> str:
    return _DRAW[name](pal).svg()


def drawn_pairs(name: str, pal) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    """(text pairs, meaningful mark pairs) actually drawn by one session, as (foreground role, background role)."""
    cv = _DRAW[name](pal)
    return cv.text_pairs, cv.mark_pairs


def minimum(fg: str, bg: str) -> float:
    """The contrast a text pair must reach: 4.5:1, or 4.0:1 for secondary text on a panel (the documented E1 exception)."""
    return 4.0 if fg == "ui.text_secondary" and bg in PANELS else 4.5
