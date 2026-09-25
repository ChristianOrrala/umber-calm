"""Minimal template language: {{ ref | filter(arg, ...) | ... }} and {{ "literal" }}."""
from __future__ import annotations

import re

from . import filters
from .palette import Palette, PaletteError

EXPR = re.compile(r"\{\{(.*?)\}\}", re.S)
FILTER = re.compile(r"^([a-z_0-9]+)(?:\((.*)\))?$", re.S)


class TemplateError(ValueError):
    pass


def _split_pipes(expr: str) -> list[str]:
    parts, buf, depth, quote = [], [], 0, None
    for ch in expr:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "|" and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    parts.append("".join(buf))
    return [p.strip() for p in parts]


def _evaluate(expr: str, pal: Palette, extra: dict[str, str], on_filter=None) -> str:
    parts = _split_pipes(expr)
    head = parts[0]
    if not head:
        raise TemplateError("empty expression")
    if len(head) >= 2 and head[0] == head[-1] and head[0] in "\"'":
        value = head[1:-1]
    elif head in extra:
        value = extra[head]
    else:
        value = pal.resolve(head)
    for part in parts[1:]:
        m = FILTER.match(part)
        if not m:
            raise TemplateError(f"malformed filter {part!r}")
        name, raw_args = m.group(1), m.group(2)
        args = [a.strip() for a in raw_args.split(",")] if raw_args and raw_args.strip() else []
        value = filters.apply(value, name, args, pal)
        if on_filter:
            on_filter(name, value)
    return value


def render(text: str, pal: Palette, *, source: str, extra: dict[str, str] | None = None) -> str:
    text = text.replace("\r\n", "\n")
    extra = extra or {}
    out, pos = [], 0
    for m in EXPR.finditer(text):
        out.append(text[pos:m.start()])
        line = text.count("\n", 0, m.start()) + 1
        try:
            out.append(_evaluate(m.group(1), pal, extra))
        except (TemplateError, PaletteError, filters.FilterError) as e:
            raise TemplateError(f"{source}:{line}: {e}") from None
        pos = m.end()
    rest = text[pos:]
    if "{{" in rest:
        line = text.count("\n", 0, pos + rest.index("{{")) + 1
        raise TemplateError(f"{source}:{line}: unclosed '{{{{'")
    out.append(rest)
    return "".join(out)


def blends(text: str, pal: Palette, *, source: str) -> list[tuple[int, str]]:
    """Every blend(...) application in a template, as (line, resulting #RRGGBB), in order."""
    text = text.replace("\r\n", "\n")
    found: list[tuple[int, str]] = []
    for m in EXPR.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        collect = lambda name, value, line=line: found.append((line, value)) if name == "blend" else None
        try:
            _evaluate(m.group(1), pal, {"meta.template": source}, collect)
        except (TemplateError, PaletteError, filters.FilterError) as e:
            raise TemplateError(f"{source}:{line}: {e}") from None
    return found
