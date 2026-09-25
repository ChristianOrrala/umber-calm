"""Extract syntax-token colors from generated theme files (red/orange rule, spec §5.1).

Extractors resolve the indirection their format allows (Sublime `var()`, Helix [palette] names, Vim `hi link`
chains). A value that does not resolve is returned as is, and `violations` reports every value that is not a
#RRGGBB color as unchecked: an extractor never skips a mapping it cannot read."""
from __future__ import annotations

import json
import plistlib
import re
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

VIM_SYNTAX_GROUPS = {
    "Comment", "Constant", "String", "Character", "Number", "Boolean", "Float", "Identifier",
    "Function", "Statement", "Conditional", "Repeat", "Label", "Operator", "Keyword", "Exception",
    "PreProc", "Include", "Define", "Macro", "PreCondit", "Type", "StorageClass", "Structure",
    "Typedef", "Special", "SpecialChar", "Tag", "Delimiter", "SpecialComment",
}
HELIX_NON_SYNTAX = ("ui.", "diagnostic", "diff.", "warning", "error", "info", "hint")
VIM_HI = re.compile(r"^hi!?\s+(\S+)(.*)$")
VIM_LINK = re.compile(r"^hi!?\s+(?:def(?:ault)?\s+)?link\s+(\S+)\s+(\S+)\s*$")
VIM_GUIFG = re.compile(r"\bguifg=(\S+)")
HEX = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")


def _vscode(text: str) -> list[str]:
    data = json.loads(text)
    out = [t["settings"]["foreground"] for t in data.get("tokenColors", []) if "foreground" in t.get("settings", {})]
    for value in data.get("semanticTokenColors", {}).values():
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, dict) and "foreground" in value:
            out.append(value["foreground"])
    return out


def _sublime(text: str) -> list[str]:
    data = json.loads(text)
    variables = data.get("variables", {})

    def resolve(value: str, seen: tuple = ()) -> str:
        m = re.fullmatch(r"\s*var\(\s*([A-Za-z0-9_.-]+)\s*\)\s*", value)
        if not m or m.group(1) in seen or not isinstance(variables.get(m.group(1)), str):
            return value
        return resolve(variables[m.group(1)], seen + (m.group(1),))
    return [resolve(r["foreground"]) for r in data.get("rules", []) if "foreground" in r]


def _zed(text: str) -> list[str]:
    out = []
    for theme in json.loads(text).get("themes", []):
        for value in theme.get("style", {}).get("syntax", {}).values():
            if isinstance(value, dict) and value.get("color"):
                out.append(value["color"])
    return out


def _helix(text: str) -> list[str]:
    data = tomllib.loads(text)
    pal = data.get("palette", {})
    out = []
    for key, value in data.items():
        if key in ("palette", "inherits") or key.startswith(HELIX_NON_SYNTAX):
            continue
        fg = value if isinstance(value, str) else value.get("fg") if isinstance(value, dict) else None
        if fg:
            out.append(pal.get(fg, fg))
    return out


def _vim(text: str) -> list[str]:
    """guifg of every syntax group, following `hi link` chains; a chain that ends nowhere or loops is returned
    as `link <group>` (unchecked). A later definition of a group replaces its earlier link or colors."""
    fg: dict[str, str | None] = {}
    links: dict[str, str] = {}
    order: list[str] = []
    for line in text.splitlines():
        link, hi = VIM_LINK.match(line), VIM_HI.match(line)
        if link:
            group, target = link.groups()
            links[group] = target
            fg.pop(group, None)
        elif hi and hi.group(1) not in ("clear", "link"):
            group = hi.group(1)
            m = VIM_GUIFG.search(hi.group(2))
            fg[group] = None if not m or m.group(1).upper() == "NONE" else m.group(1)
            links.pop(group, None)
        else:
            continue
        if group not in order:
            order.append(group)

    def resolve(group: str, seen: tuple = ()) -> str | None:
        if group in fg:
            return fg[group]
        if group in links and links[group] not in seen:
            return resolve(links[group], seen + (group,))
        return f"link {seen[0] if seen else group}"
    return [v for g in order if g in VIM_SYNTAX_GROUPS for v in [resolve(g)] if v is not None]


TMTHEME_DIFF_SCOPES = ("markup.inserted", "markup.deleted", "markup.changed")


def _tmtheme(data: bytes) -> list[str]:
    entries = plistlib.loads(data).get("settings", [])[1:]
    return [e["settings"]["foreground"] for e in entries
            if "foreground" in e.get("settings", {}) and not e.get("scope", "").startswith(TMTHEME_DIFF_SCOPES)]


def _text(fn):
    return lambda data: fn(data.decode("utf-8"))


FISH_SYNTAX = ("normal", "command", "keyword", "quote", "redirection", "end", "param", "option",
               "comment", "operator", "escape")
FISH_LINE = re.compile(r"^fish_color_([a-z_]+)((?:[ \t]+\S+)*)[ \t]*$", re.M)
FISH_HEX = re.compile(r"[0-9A-Fa-f]{6}")
CSS_CODE_VAR = re.compile(r"--code-[a-z-]+:\s*(#[0-9A-Fa-f]{6})")


# <attributes> keys that hold non-syntax editor colors rather than code-token colors: diagnostics (errors,
# warnings), the search-match highlight, the base editor text/background, and a debugger value display. Every
# other <attributes> key — every DEFAULT_* language-highlighter key and every language-specific Darcula override
# this scheme maps — is a syntax-token mapping and must be read.
JETBRAINS_NON_SYNTAX = {"TEXT", "ERRORS_ATTRIBUTES", "WARNING_ATTRIBUTES", "SEARCH_RESULT_ATTRIBUTES",
                        "KOTLIN_COROUTINE_DEBUGGER_VALUE"}


def _jetbrains(text: str) -> list[str]:
    attributes = ET.fromstring(text).find("attributes")
    out = []
    for option in [] if attributes is None else attributes:
        if option.get("name") in JETBRAINS_NON_SYNTAX:
            continue
        for sub in option.iter("option"):
            if sub.get("name") == "FOREGROUND" and sub.get("value"):
                out.append("#" + sub.get("value").upper())
    return out


def _fish(text: str) -> list[str]:
    out = []
    for name, args in FISH_LINE.findall(text):
        if name in FISH_SYNTAX:
            out += ["#" + a.upper() for a in args.split() if FISH_HEX.fullmatch(a)]
    return out


def _obsidian(text: str) -> list[str]:
    return CSS_CODE_VAR.findall(text)


def _opencode(text: str) -> list[str]:
    theme = json.loads(text).get("theme", {})
    return [v for k, v in theme.items() if k.startswith(("syntax", "markdown")) and isinstance(v, str)]


# Format -> extractor(bytes) -> colors used by syntax mappings. Later tasks add formats here.
EXTRACTORS = {
    "vscode": _text(_vscode),
    "sublime": _text(_sublime),
    "zed": _text(_zed),
    "helix": _text(_helix),
    "vim": _text(_vim),
    "tmtheme": _tmtheme,
    "jetbrains": _text(_jetbrains),
    "fish": _text(_fish),
    "obsidian": _text(_obsidian),
    "opencode": _text(_opencode),
}


def extract(fmt: str, data: bytes) -> list[str]:
    return EXTRACTORS[fmt](data)


def violations(fmt: str, path: Path, reserved: dict[str, str]) -> list[str]:
    bad = {hx.upper(): name for name, hx in reserved.items()}
    found = []
    for value in extract(fmt, Path(path).read_bytes()):
        if not HEX.fullmatch(value):
            found.append(f"{Path(path).name}: syntax value {value!r} does not resolve to #RRGGBB (unchecked)")
            continue
        key = value.upper()[:7]
        if key in bad:
            found.append(f"{Path(path).name} uses reserved {bad[key]} ({value}) in a syntax mapping")
    return found
