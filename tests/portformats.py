"""Standard-library structural validators for generated port files (spec §8.1.3).

They check shape (sections, keys, value syntax, palette lengths), not application behavior;
application behavior is what verification tiers record."""
from __future__ import annotations

import configparser
import re

HEX6 = re.compile(r"#[0-9A-Fa-f]{6}")
HEX_ANY = re.compile(r"#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})")


def ini(text: str, *, sectionless: bool = False) -> configparser.ConfigParser:
    """Parse INI-like text strictly (duplicate sections or keys raise). Keys keep their case."""
    cp = configparser.ConfigParser(interpolation=None, strict=True, comment_prefixes=("#", ";"),
                                   inline_comment_prefixes=None)
    cp.optionxform = str
    cp.read_string(("[root]\n" if sectionless else "") + text)
    return cp


def line_problems(text: str, line_re: re.Pattern) -> list[str]:
    """Lines (ignoring blanks and # comments) that do not fully match line_re."""
    return [f"line {n}: {line!r}" for n, line in enumerate(text.splitlines(), 1)
            if line.strip() and not line.lstrip().startswith("#") and not line_re.fullmatch(line)]


def non_hex(values, pattern: re.Pattern = HEX_ANY) -> list:
    """Values that are not hex colors (#RRGGBB or #RRGGBBAA by default)."""
    return [v for v in values if not (isinstance(v, str) and pattern.fullmatch(v))]


def keys_in(path_text: str) -> set[str]:
    """Read a committed key-list fixture (one key per line)."""
    return {line.strip() for line in path_text.splitlines() if line.strip()}


# Zellij 0.45.1 component theme format (zellij-utils/src/kdl/mod.rs: Themes::from_kdl, style_declaration_from_node).
ZELLIJ_COMPONENTS = ("text_unselected", "text_selected", "ribbon_selected", "ribbon_unselected", "table_title",
                     "table_cell_selected", "table_cell_unselected", "list_selected", "list_unselected",
                     "frame_selected", "frame_unselected", "frame_highlight", "exit_code_success", "exit_code_error",
                     "multiplayer_user_colors")
ZELLIJ_STYLE_KEYS = ("base", "background", "emphasis_0", "emphasis_1", "emphasis_2", "emphasis_3")
ZELLIJ_PLAYERS = tuple(f"player_{i}" for i in range(1, 11))


def zellij_components(text: str) -> dict[str, dict[str, str]]:
    """{component: {key: value}} of the single theme in a `themes { <name> { <component> { key "value" } } }` file."""
    body = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("//")]
    assert body[0] == "themes {" and body[1].endswith(" {") and body[-2:] == ["}", "}"], body[:2] + body[-2:]
    theme: dict[str, dict[str, str]] = {}
    current = None
    for line in body[2:-2]:
        if line.endswith(" {"):
            current = theme.setdefault(line[:-2], {})
        elif line == "}":
            current = None
        else:
            key, value = line.split(" ", 1)
            current[key] = value.strip('"')
    return theme
