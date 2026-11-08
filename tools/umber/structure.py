"""Structural validators for generated files that no standard parser checks (spec §8.1 item 3).

`checks._format_problems` runs `problems()` on every generated file. RULES maps an output path pattern
(fnmatch, repository-relative) to validators; each validator takes (root, text) and returns problems. They check
shape — INI sections and palette lengths, KDL and tmux line grammars, the YAML subsets we emit, and app schemas
(keys against committed upstream key lists) — never application behavior, which verification records."""
from __future__ import annotations

import base64
import configparser
import fnmatch
import json
import os
import re
import shutil
import subprocess
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable

HEX = "#[0-9A-F]{6}"
Validator = Callable[[Path, str], list[str]]


def ini(text: str, *, sectionless: bool = False) -> configparser.ConfigParser:
    """Parse INI-like text strictly (duplicate sections or keys raise). Keys keep their case."""
    cp = configparser.ConfigParser(interpolation=None, strict=True, comment_prefixes=("#", ";"),
                                   inline_comment_prefixes=None)
    cp.optionxform = str
    cp.read_string(("[root]\n" if sectionless else "") + text)
    return cp


def _body(text: str, comment: str) -> list[tuple[int, str]]:
    return [(n, line) for n, line in enumerate(text.splitlines(), 1)
            if line.strip() and not line.lstrip().startswith(comment)]


def lines(pattern: str, comment: str = "#") -> Validator:
    """Every non-blank, non-comment line fully matches `pattern` (reported by line number, never content)."""
    rx = re.compile(pattern)
    return lambda root, text: [f"line {n} does not match {pattern!r}" for n, line in _body(text, comment)
                               if not rx.fullmatch(line)]


def sections(*names: str, ordered: bool = True) -> Validator:
    """The INI file has exactly these sections (in this order when `ordered`)."""
    def check(root: Path, text: str) -> list[str]:
        found = ini(text).sections()
        same = found == list(names) if ordered else set(found) == set(names)
        return [] if same else [f"sections {found} are not {list(names)}"]
    return check


def slots(section: str | None, key_pattern: str, n: int, value_pattern: str) -> Validator:
    """Exactly `n` keys matching key_pattern in `section` (None = a sectionless file), each value value_pattern."""
    def check(root: Path, text: str) -> list[str]:
        table = ini(text, sectionless=section is None)[section or "root"]
        keys = [k for k in table if re.fullmatch(key_pattern, k)]
        found = [] if len(keys) == n else [f"[{section or 'root'}] has {len(keys)} keys matching {key_pattern!r}, not {n}"]
        return found + [f"[{section or 'root'}] {k} is not {value_pattern!r}" for k in keys
                        if not re.fullmatch(value_pattern, table[k])]
    return check


def entries(section: str, key: str, n: int, sep: str, value_pattern: str) -> Validator:
    """`[section] key` exists and is a `sep`-separated list of exactly `n` entries, each value_pattern."""
    def check(root: Path, text: str) -> list[str]:
        items = ini(text)[section][key].split(sep)
        found = [] if len(items) == n else [f"[{section}] {key} has {len(items)} entries, not {n}"]
        return found + [f"[{section}] {key}: entry {i} is not {value_pattern!r}" for i, v in enumerate(items, 1)
                        if not re.fullmatch(value_pattern, v)]
    return check


def values(section: str, value_pattern: str) -> Validator:
    """Every value of `[section]` fully matches value_pattern."""
    def check(root: Path, text: str) -> list[str]:
        return [f"[{section}] {k} is not {value_pattern!r}" for k, v in ini(text)[section].items()
                if not re.fullmatch(value_pattern, v)]
    return check


# Zellij's component theme format (0.45.1, zellij-utils/src/kdl/mod.rs): components with a base, a background and
# four emphasis colors, plus up to ten multiplayer colors.
ZELLIJ_COMPONENTS = {"text_unselected", "text_selected", "ribbon_selected", "ribbon_unselected", "table_title",
                     "table_cell_selected", "table_cell_unselected", "list_selected", "list_unselected",
                     "frame_selected", "frame_unselected", "frame_highlight", "exit_code_success", "exit_code_error"}
ZELLIJ_STYLE_KEYS = ["base", "background", "emphasis_0", "emphasis_1", "emphasis_2", "emphasis_3"]


def _zellij(root: Path, text: str) -> list[str]:
    body = [line for _, line in _body(text, "//")]
    if body[:2] != ["themes {", "    umber-calm {"] or body[-2:] != ["    }", "}"]:
        return ["expected `themes {` / `    umber-calm {` … `    }` / `}`"]
    problems, component, keys = [], None, []
    for i, line in enumerate(body[2:-2], 1):
        opening = re.fullmatch(r"        ([a-z0-9_]+) \{", line)
        entry = re.fullmatch(rf'            ([a-z0-9_]+) "{HEX}"', line)
        if opening and component is None:
            component, keys = opening.group(1), []
            if component not in ZELLIJ_COMPONENTS | {"multiplayer_user_colors"}:
                problems.append(f"unknown component {component!r}")
        elif line == "        }" and component is not None:
            expected = ([f"player_{n}" for n in range(1, 11)] if component == "multiplayer_user_colors"
                        else ZELLIJ_STYLE_KEYS)
            if keys != expected:
                problems.append(f"{component} has keys {keys}, not {expected}")
            component = None
        elif entry and component is not None:
            keys.append(entry.group(1))
        else:
            problems.append(f"theme line {i} is not a component opening, a `key \"#RRGGBB\"` entry or a closing brace")
    return problems + (["unclosed component"] if component else [])


def _count(pattern: str, n: int) -> Validator:
    """Exactly `n` lines fully match `pattern`."""
    rx = re.compile(pattern)
    def check(root: Path, text: str) -> list[str]:
        found = sum(1 for _, line in _body(text, "#") if rx.fullmatch(line))
        return [] if found == n else [f"{found} lines match {pattern!r}, not {n}"]
    return check


def _css(root: Path, text: str) -> list[str]:
    """CSS-like syntax (CSS, GTK CSS, rasi): comments closed, `@define-color name value;` statements, and
    `selector { name: value; … }` blocks, one level deep, every declaration `name: value;`."""
    if text.count("/*") != text.count("*/"):
        return ["unterminated comment"]
    body = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    problems, depth, pos = [], 0, 0
    for m in re.finditer(r"[{};]", body):
        chunk = body[pos:m.start()].strip()
        pos = m.end()
        token = m.group(0)
        if token == "{":
            if depth or not chunk:
                problems.append(f"unexpected '{{' after {chunk[:40]!r}")
            depth += 1
        elif token == "}":
            if chunk:
                problems.append(f"declaration {chunk[:40]!r} is not terminated by ';'")
            if not depth:
                problems.append("unbalanced '}'")
            depth = max(depth - 1, 0)
        elif depth and not re.fullmatch(r"[-A-Za-z0-9_]+[ \t]*:[ \t]*[^:;{}\n]+", chunk):
            problems.append(f"malformed declaration {chunk[:40]!r}")
        elif not depth and not re.fullmatch(r"@define-color\s+[A-Za-z0-9_-]+\s+\S+", chunk):
            problems.append(f"malformed statement {chunk[:40]!r}")
    if body[pos:].strip():
        problems.append("text after the last block or statement")
    return problems + (["unclosed block"] if depth else [])


VIM_LINE = re.compile(r"""hi clear|hi!? link [A-Za-z@.]+ [A-Za-z@.]+|hi [A-Za-z@.]+( (gui|cterm)(fg|bg|sp)?=[^\s=]+)+"""
                      r"""|set background=dark|let g:colors_name = "umber-calm"|if exists\("syntax_on"\) \| syntax reset \| endif"""
                      r"""|if has\('nvim'\)|  lua require\('umber-calm'\)\.load\(\)|  finish|endif""")


def _vim(root: Path, text: str) -> list[str]:
    problems = [f"line {n} is not a colorscheme statement" for n, line in _body(text, '"') if not VIM_LINE.fullmatch(line)]
    opened = sum(1 for _, line in _body(text, '"') if line.startswith("if ") and not line.endswith("endif"))
    closed = sum(1 for _, line in _body(text, '"') if line == "endif")
    return problems + ([] if opened == closed else [f"{opened} if blocks but {closed} endif"])


def _lua_table(root: Path, text: str) -> list[str]:
    """A Lua file that returns one table literal: strings closed, brackets balanced, nothing after the table."""
    code = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', text)
    if '"' in code.replace('""', ""):
        return ["unterminated string"]
    code = re.sub(r"--[^\n]*", "", code).strip()
    if not code.startswith("return {"):
        return ["does not return a table"]
    depth = 0
    for i, ch in enumerate(code):
        depth += {"{": 1, "[": 1, "(": 1, "}": -1, "]": -1, ")": -1}.get(ch, 0)
        if depth < 0:
            return ["unbalanced brackets"]
        if depth == 0 and i > len("return "):
            return [] if not code[i + 1:].strip() else ["text after the returned table"]
    return ["unclosed table"]


def _bash(root: Path, text: str) -> list[str]:
    """`bash -n` (parse only, nothing runs). Windows is skipped: `bash` there may be the WSL launcher; the macOS
    and Linux CI legs check the same bytes."""
    if os.name == "nt":
        return []
    bash = shutil.which("bash")
    if bash is None:
        return ["cannot check shell syntax: bash not found"]
    result = subprocess.run([bash, "-n"], input=text.encode("utf-8"), capture_output=True)
    return [] if result.returncode == 0 else ["bash -n reports a syntax error"]


def _fixture(root: Path, name: str) -> set[str]:
    path = Path(root) / "tests/fixtures" / name
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _zed(root: Path, text: str) -> list[str]:
    known = _fixture(root, "zed-theme-v0.2.0-keys.txt")
    problems = []
    for theme in json.loads(text).get("themes", []):
        style = theme.get("style", {})
        problems += [f"unknown Zed style key {k!r}" for k in sorted(set(style) - known)]
        problems += [f"unknown Zed syntax property {k!r}"
                     for k in sorted({k for v in style.get("syntax", {}).values() for k in v} - known)]
    return problems


def _yazi(root: Path, text: str) -> list[str]:
    known = _fixture(root, "yazi-25.5.28-theme-keys.txt")
    data = tomllib.loads(text)
    ours = {f"{s}.{k}" for s, t in data.items() if s != "filetype" and isinstance(t, dict) for k in t}
    ours |= {f"filetype.rules[].{k}" for rule in data.get("filetype", {}).get("rules", []) for k in rule}
    return [f"unknown yazi 25.5.28 theme key {k!r}" for k in sorted(ours - known)]


def _herdr(root: Path, text: str) -> list[str]:
    """Herdr TUI 0.9.1 (src/config/theme.rs, CustomThemeColors): [theme] plus every [theme.custom] token, in hex."""
    known = _fixture(root, "herdr-0.9.1-theme-keys.txt")
    data = tomllib.loads(text)
    theme = data.get("theme", {})
    custom = theme.get("custom", {})
    problems = [f"unexpected top-level table {k!r} (the port only sets [theme])" for k in sorted(set(data) - {"theme"})]
    problems += [f"unknown Herdr TUI 0.9.1 theme token {k!r}" for k in sorted(set(custom) - known)]
    problems += [f"Herdr TUI 0.9.1 theme token {k!r} is not set (the base theme would show through)" for k in sorted(known - set(custom))]
    problems += [f"theme.custom.{k} = {v!r} is not #RRGGBB" for k, v in sorted(custom.items())
                 if not (isinstance(v, str) and re.fullmatch(HEX, v))]
    return problems


def _json_with_duplicates(text: str) -> tuple[object, list[str]]:
    """Parse JSON while recording duplicate object keys at every depth."""
    duplicates = []

    def pairs(items):
        seen = {}
        for k, v in items:
            if k in seen:
                duplicates.append(k)
            seen[k] = v
        return seen

    return json.loads(text, object_pairs_hook=pairs), duplicates


HERDR_APP_TOP = ("background", "foreground", "selection", "cursor", "ansi", "colors")
HERDR_APP_COLORS = {"foreground", "surface", "canvas", "chrome", "popover", "raised", "hover", "selected",
                    "border", "input", "ring", "muted", "dim", "accent", "accent_foreground", "solid",
                    "solid_foreground", "working", "blocked", "done", "idle", "unknown"}
HERDR_APP_ALPHA_OK = {"hover", "selected"}


def _herdr_app(root: Path, text: str) -> list[str]:
    """Herdr app 0.1.12 (src/settings.rs ThemeFile and resolve() at tag v0.1.12)."""
    data, duplicates = _json_with_duplicates(text)
    problems = [f"duplicate key {k!r}" for k in duplicates]
    if not isinstance(data, dict):
        return problems + ["the theme must be a JSON object"]
    problems += [f"unexpected top-level key {k!r} (Herdr refuses the whole theme)"
                 for k in sorted(set(data) - set(HERDR_APP_TOP))]
    problems += [f"missing top-level key {k!r}" for k in HERDR_APP_TOP if k not in data]
    for k in HERDR_APP_TOP[:4]:
        if k in data and not (isinstance(data[k], str) and re.fullmatch(HEX, data[k])):
            problems.append(f"{k} is not #RRGGBB")
    ansi = data.get("ansi")
    if not isinstance(ansi, list):
        problems.append("ansi must be a list")
    else:
        if len(ansi) != 16:
            problems.append("ansi must have exactly 16 entries")
        problems += [f"ansi[{i}] is not #RRGGBB" for i, v in enumerate(ansi)
                     if not (isinstance(v, str) and re.fullmatch(HEX, v))]
    colors = data.get("colors")
    if not isinstance(colors, dict):
        problems.append("colors must be a JSON object")
        colors = {}
    problems += [f"unknown Herdr color {k!r}" for k in sorted(set(colors) - HERDR_APP_COLORS)]
    problems += [f"color {k!r} is not set (Herdr would derive it)" for k in sorted(HERDR_APP_COLORS - set(colors))]
    for k, v in sorted(colors.items()):
        pattern, label = (r"#[0-9A-F]{8}", "#RRGGBBAA") if k in HERDR_APP_ALPHA_OK else (HEX, "#RRGGBB")
        if not (isinstance(v, str) and re.fullmatch(pattern, v)):
            problems.append(f"colors.{k} is not {label}")
    covered = {k for k in ("background", "selection", "cursor") if k in data} | set(colors)
    if "foreground" in data:
        covered.add("terminal_foreground")
    if isinstance(ansi, list):
        covered.update(f"ansi{i}" for i in range(len(ansi)))
    known = _fixture(root, "herdr-app-0.1.12-theme-keys.txt")
    problems += [f"resolved name {k!r} is not covered (Herdr would derive it)" for k in sorted(known - covered)]
    return problems


MOSHI_TOP = ("v", "name", "mode", "colors")
MOSHI_HEX = "#[0-9a-f]{6}"  # Moshi reads #rrggbb or #rgb; the port writes #rrggbb in lowercase, as its gallery does


def _moshi(root: Path, text: str) -> list[str]:
    """Moshi theme format v1 (getmoshi.app/docs/personalization, "Custom themes"; key list in the fixture)."""
    data, duplicates = _json_with_duplicates(text)
    problems = [f"duplicate key {k!r}" for k in duplicates]
    if not isinstance(data, dict):
        return problems + ["the theme must be a JSON object"]
    problems += [f"unexpected top-level key {k!r}" for k in sorted(set(data) - set(MOSHI_TOP))]
    problems += [f"missing top-level key {k!r}" for k in MOSHI_TOP if k not in data]
    if "v" in data and not (type(data["v"]) is int and data["v"] == 1):  # not true, not 1.0
        problems.append("v must be 1")
    if "name" in data and not (isinstance(data["name"], str) and 1 <= len(data["name"]) <= 40):
        problems.append("name must be 1 to 40 characters")
    if "mode" in data and data["mode"] not in ("dark", "light"):
        problems.append("mode must be 'dark' or 'light' (Moshi never guesses it)")
    colors = data.get("colors", {})
    if not isinstance(colors, dict):
        return problems + ["colors must be a JSON object"]
    known = _fixture(root, "moshi-theme-v1-keys.txt")
    problems += [f"unknown Moshi color {k!r}" for k in sorted(set(colors) - known)]
    problems += [f"color {k!r} is not set (Moshi would derive it)" for k in sorted(known - {"bold"} - set(colors))]
    for k, v in sorted(colors.items()):
        if k == "bold":
            if not (v == "bright" or (isinstance(v, str) and re.fullmatch(MOSHI_HEX, v))):
                problems.append("colors.bold is not #rrggbb or 'bright'")
        elif not (isinstance(v, str) and re.fullmatch(MOSHI_HEX, v)):
            problems.append(f"colors.{k} is not #rrggbb")
    return problems


def _moshi_import(root: Path, text: str) -> list[str]:
    """The paste string: `moshi-theme:` and the compact theme JSON in base64url without padding, on one line."""
    m = re.fullmatch(r"moshi-theme:([A-Za-z0-9_-]+)\n", text)
    if not m:
        return ["must be one line: moshi-theme: and base64url without padding"]
    encoded = m.group(1)
    try:
        theme = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode("utf-8")
        json.loads(theme)
    except (ValueError, UnicodeDecodeError):  # binascii.Error and JSONDecodeError are ValueErrors
        return ["the payload is not base64url of UTF-8 JSON"]
    return [f"payload: {p}" for p in _moshi(root, theme)]


FRESH_SECTIONS = ("editor", "ui", "search", "diagnostic", "syntax")
FRESH_LEGACY = {"editor.selection_modifier", "ui.semantic_highlight_modifier"}  # superseded by bundled attributes
FRESH_MODIFIER_KEYS = {"editor.bracket_rainbow_match_modifier"}
FRESH_MODIFIERS = {"bold", "italic", "underlined", "dim", "reversed"}


def _fresh_rgb(value) -> bool:
    return (isinstance(value, list) and len(value) == 3
            and all(isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 255 for c in value))


def _fresh_modifiers(value) -> bool:
    return isinstance(value, list) and all(isinstance(m, str) and m in FRESH_MODIFIERS for m in value)


def _fresh(root: Path, text: str) -> list[str]:
    """Fresh 0.5.4 (crates/fresh-editor/plugins/schemas/theme.schema.json at tag v0.5.4): a standalone theme that sets
    every color key as [r, g, b] or {"color": [r, g, b], "modifier": [...]}. One unreadable value makes Fresh drop the
    whole theme, so every value is checked."""
    data, duplicates = _json_with_duplicates(text)
    if not isinstance(data, dict):
        return ["the theme must be a JSON object"]
    problems = [f"duplicate key {k!r}" for k in duplicates]
    for k in sorted(set(data) - {"name", *FRESH_SECTIONS}):
        problems.append("the port is standalone: no extends" if k == "extends" else f"unexpected top-level key {k!r}")
    if not (isinstance(data.get("name"), str) and data["name"]):
        problems.append("name must be a non-empty string")
    problems += [f"section {s!r} must be a JSON object" for s in FRESH_SECTIONS if not isinstance(data.get(s, {}), dict)]
    values = {f"{s}.{k}": v for s in FRESH_SECTIONS if isinstance(data.get(s, {}), dict)
              for k, v in data.get(s, {}).items()}
    known = _fixture(root, "fresh-0.5.4-theme-keys.txt")
    problems += [f"unknown Fresh 0.5.4 theme key {k!r}" for k in sorted(set(values) - known)]
    problems += [f"Fresh theme key {k!r} is not set (Fresh would fall back to a color the port did not choose)"
                 for k in sorted(known - FRESH_LEGACY - set(values))]
    for k, v in sorted(values.items()):
        if k in FRESH_MODIFIER_KEYS or k in FRESH_LEGACY:
            if not _fresh_modifiers(v):
                problems.append(f"{k} must be a list of {sorted(FRESH_MODIFIERS)}")
            continue
        color = v.get("color") if isinstance(v, dict) else v
        if isinstance(v, dict) and (set(v) - {"color", "modifier"} or not _fresh_modifiers(v.get("modifier", []))):
            problems.append(f"{k} must be {{color, modifier}} with modifiers from {sorted(FRESH_MODIFIERS)}")
        if not _fresh_rgb(color):  # names, "Default" included (Color::Reset), are never the port's colors
            problems.append(f"{k} is not [r, g, b] with channels 0-255")
    return problems


# OpenCode 2.2.5 theme documents (packages/theme/src/tui/{schema,expand,resolve}.ts at tag v2.2.5). A file with "base"
# is used as written; a flat "theme" file goes through migrateV1, which generates the scales the TUI draws from.
OPENCODE_STEPS = ("100", "200", "300", "400", "500", "600", "700", "800", "900")
OPENCODE_HUE_REF = re.compile(r"\$hue\.(.+)\.(100|200|300|400|500|600|700|800|900)")
OPENCODE_HEX = re.compile(r"#(?:[\da-f]{3}|[\da-f]{4}|[\da-f]{6}|[\da-f]{8})", re.I)
OPENCODE_STATES = ("disabled", "pressed", "focused", "selected", "hovered")
OPENCODE_SURFACE_KEYS = ("text", "background", "border", "scrollbar", "diff", "syntax", "markdown")


def _opencode_leaves(node: dict, prefix: str = "") -> dict[str, object]:
    found: dict[str, object] = {}
    for key, value in node.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            found.update(_opencode_leaves(value, f"{path}."))
        else:
            found[path] = value
    return found


def _opencode_merge(*values: dict) -> dict:
    merged: dict = {}
    for value in values:
        for key, item in value.items():
            merged[key] = _opencode_merge(merged.get(key, {}), item) if isinstance(item, dict) else item
    return merged


def _opencode_expand_states(group: dict | None, path: str) -> dict | None:
    if not group or "base" not in group:
        return group
    return {**group, **{f"${s}": group.get(f"${s}", f"${path}.base") for s in OPENCODE_STATES}}


def _opencode_expand(tokens: dict) -> dict:
    """expand.ts: defaults for what a document may leave out."""
    tokens = dict(tokens)
    if "text" in tokens:
        text = dict(tokens["text"])
        if "base" in text:
            text.setdefault("muted", "$text.base")
        if "muted" in text or "base" in text:
            text.setdefault("faint", "$text.muted")
        if "formfield" in text:
            text["formfield"] = _opencode_expand_states(text["formfield"], "text.formfield")
        if "action" in text:
            text["action"] = {v: _opencode_expand_states(g, f"text.action.{v}") for v, g in text["action"].items()}
        if "feedback" in text:
            text["feedback"] = {k: ({**f, "muted": f.get("muted", f"$text.feedback.{k}.base")} if "base" in f else f)
                                for k, f in text["feedback"].items()}
        tokens["text"] = text
    if "background" in tokens:
        background = dict(tokens["background"])
        if "formfield" in background:
            background["formfield"] = _opencode_expand_states(background["formfield"], "background.formfield")
        if "action" in background:
            background["action"] = {v: _opencode_expand_states(g, f"background.action.{v}")
                                    for v, g in background["action"].items()}
        tokens["background"] = background
    return tokens


def _opencode_contextual_actions(base: dict | None, surface: dict | None) -> dict:
    """resolve.ts contextualActions: a surface's own state, then its base, then the page's state, then the page's base."""
    result = {}
    for variant in ("primary", "secondary", "destructive"):
        page, own = (base or {}).get(variant) or {}, (surface or {}).get(variant) or {}
        states = {"base": own.get("base", page.get("base"))}
        for state in OPENCODE_STATES:
            key = f"${state}"
            states[key] = own.get(key, own.get("base", page.get(key, page.get("base"))))
        result[variant] = states
    return result


def _opencode_contextualize(base: dict, override: dict) -> dict:
    merged = _opencode_merge(base, override)
    for section in ("text", "background"):
        merged[section]["action"] = _opencode_contextual_actions(base.get(section, {}).get("action"),
                                                                 override.get(section, {}).get("action"))
    return merged


def opencode_hues(document: dict) -> dict[str, dict[str, str]]:
    """resolve.ts resolveHue for the dark mode: each hue's nine steps; a "$hue.name" alias takes its target's steps."""
    source = document["dark"]["hue"]

    def resolve(name: str, chain: tuple[str, ...]) -> dict[str, str]:
        if name in chain:
            raise ValueError(f"circular hue reference: {' -> '.join((*chain, name))}")
        if name not in source:
            raise ValueError(f"hue {name!r} was not found")
        value = source[name]
        if isinstance(value, str):
            if not value.startswith("$hue."):
                raise ValueError(f"hue alias {value!r} must reference a hue scale")
            return resolve(value[5:], (*chain, name))
        if not isinstance(value, dict) or set(value) != set(OPENCODE_STEPS):
            raise ValueError(f"hue {name!r} must set exactly the steps {', '.join(OPENCODE_STEPS)}")
        for step, color in value.items():
            if not (isinstance(color, str) and OPENCODE_HEX.fullmatch(color)):
                raise ValueError(f"hue.{name}.{step} is not a hex color")
        return value

    return {name: resolve(name, ()) for name in source}


def opencode_view(document: dict, surface: str | None = None) -> dict[str, str]:
    """What the TUI reads for a document's dark mode, every token resolved to a color: the page, or surface "dialog"
    (or "dialog.footer"). "transparent" stays "transparent". Raises ValueError where resolve.ts would throw."""
    hues = opencode_hues(document)
    merged = _opencode_merge(document["base"], {k: v for k, v in document["dark"].items() if k != "hue"})
    page = _opencode_expand({k: merged[k] for k in OPENCODE_SURFACE_KEYS if k in merged})
    tokens = page
    if surface:
        dialog = merged.get("@dialog", {})
        expanded = _opencode_expand({k: dialog[k] for k in OPENCODE_SURFACE_KEYS if k in dialog})
        tokens = _opencode_contextualize(page, expanded)
        if surface == "dialog.footer" and "@footer" in dialog:
            tokens = _opencode_contextualize(tokens, dialog["@footer"])

    def read(path: str) -> object:
        ref = OPENCODE_HUE_REF.fullmatch(f"${path}")
        if ref:
            if ref[1] not in hues:
                raise ValueError(f"theme reference ${path} was not found")
            return hues[ref[1]][ref[2]]
        value: object = tokens
        for key in path.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        if value is None:
            raise ValueError(f"theme reference ${path} was not found")
        return value

    def resolve(value: object, chain: tuple[str, ...] = ()) -> str:
        if not isinstance(value, str):
            raise ValueError(f"theme reference ${chain[-1] if chain else '?'} is not a color")
        if value == "transparent" or OPENCODE_HEX.fullmatch(value):
            return value
        if not value.startswith("$"):
            raise ValueError(f"invalid color {value!r}")
        target = value[1:]
        if target in chain:
            raise ValueError(f"circular theme reference: {' -> '.join((*chain, target))}")
        return resolve(read(target), (*chain, target))

    return {path: resolve(value) for path, value in _opencode_leaves(tokens).items()}


def opencode_document_problems(data: dict, known_lines: set[str]) -> list[str]:
    """schema.ts ThemeDocument for a document with a dark mode. `known_lines` lists every token path: required ones
    bare, optional ones ending in " ?"."""
    if not isinstance(data.get("base"), dict):
        return ["base must be a JSON object"]
    if not isinstance(data.get("dark"), dict) or not isinstance(data["dark"].get("hue"), dict):
        return ["dark must be a JSON object with a hue section"]
    base, hue = data["base"], data["dark"]["hue"]
    problems = [f"hue {name!r} is required" for name in ("accent", "interactive", "neutral") if name not in hue]
    categorical = base.get("categorical")
    if not (isinstance(categorical, list) and categorical and all(isinstance(c, str) and c for c in categorical)):
        problems.append("categorical must be a non-empty list of hue names")
    else:
        problems += [f"categorical hue {c!r} was not found" for c in categorical if c not in hue]
    required = {k for k in known_lines if not k.endswith(" ?")}
    known = required | {k[:-2] for k in known_lines if k.endswith(" ?")}
    dialog = base.get("@dialog", {})
    if not isinstance(dialog, dict):
        return [*problems, "@dialog must be a JSON object"]
    for prefix, tokens in (("", {k: v for k, v in base.items() if k not in ("categorical", "@dialog")}),
                           ("@dialog.", {k: v for k, v in dialog.items() if k != "@footer"}),
                           ("@dialog.@footer.", dialog.get("@footer", {}))):
        if not isinstance(tokens, dict):
            problems.append(f"{prefix or 'base'} must be a JSON object")
            continue
        leaves = _opencode_leaves(tokens)
        problems += [f"unknown OpenCode 2.2.5 theme key {prefix + k!r}" for k in sorted(set(leaves) - known)]
        if not prefix:
            problems += [f"OpenCode theme key {k!r} is not set (OpenCode would refuse the theme)"
                         for k in sorted(required - set(leaves))]
        for k, v in sorted(leaves.items()):
            if k not in known:
                continue
            if not isinstance(v, str):
                problems.append(f"{prefix}{k} must be a string")
            elif k.startswith(("syntax.", "markdown.")):
                if not (OPENCODE_HEX.fullmatch(v) or OPENCODE_HUE_REF.fullmatch(v)):
                    problems.append(f"{prefix}{k} must be a hex color or a $hue.<name>.<step> reference")
            elif not (v == "transparent" or OPENCODE_HEX.fullmatch(v) or (v.startswith("$") and len(v) > 1)):
                problems.append(f"{prefix}{k} must be a hex color, transparent or a $reference")
    if problems:
        return problems
    try:
        for surface in (None, "dialog", "dialog.footer"):
            opencode_view(data, surface)
    except ValueError as error:
        problems.append(str(error))
    return problems


def _opencode(root: Path, text: str) -> list[str]:
    """OpenCode 2.2.5: a dark-only v2 document. The TUI keeps it in a light terminal (select.ts falls back to the one
    mode), and every color is written out, so nothing comes from migrateV1's generated scales."""
    data, duplicates = _json_with_duplicates(text)
    if not isinstance(data, dict):
        return ["the theme must be a JSON object"]
    problems = [f"duplicate key {k!r}" for k in duplicates]
    if "theme" in data:
        problems.append("a flat theme is migrated into generated colors: the port is a v2 document (base and dark)")
    if "light" in data:
        problems.append("the port is dark only: no light mode")
    problems += [f"unexpected top-level key {k!r}" for k in sorted(set(data) - {"base", "dark", "theme", "light"})]
    problems += opencode_document_problems(data, _fixture(root, "opencode-2.2.5-theme-keys.txt"))
    for path, value in _opencode_leaves({k: v for k, v in data.items() if isinstance(v, dict)}).items():
        if isinstance(value, str) and value.startswith("#") and not re.fullmatch(HEX, value):
            problems.append(f"{path} is not #RRGGBB")
    return problems


# Kiro Crew 0.9.0 theme packs (src/kiro_crew/dashboard/theme_validate.py): the installer refuses any file it does not
# know, so the port ships only the level-0 files plus its README (installed as the pack's readme.md).
KIRO_CREW_FILES = {"theme.json", "variables.json", "README.md"}
KIRO_CREW_VALUE = re.compile(r"[a-zA-Z0-9#(),.\- %/]{1,200}")  # _CSS_VALUE_ALLOWED_RE and the 200-character cap
KIRO_CREW_FUNCS = re.compile(r"(?:url|expression|image|image-set|paint|element)\s*\(", re.I)


def _kiro_crew_theme(root: Path, text: str) -> list[str]:
    data = json.loads(text)
    problems = [f"unexpected key {k!r}" for k in sorted(set(data) - {"formatVersion", "slug", "name", "emoji", "level"})]
    if data.get("formatVersion") != 1 or isinstance(data.get("formatVersion"), bool):
        problems.append("formatVersion must be the integer 1")
    if data.get("level") != 0 or isinstance(data.get("level"), bool):
        problems.append("level must be 0 (the port ships only theme.json and variables.json)")
    if not (isinstance(data.get("name"), str) and 0 < len(data["name"]) <= 60):
        problems.append("name must be 1 to 60 characters")
    if not (isinstance(data.get("slug"), str) and re.fullmatch(r"[a-z0-9-]{1,40}", data["slug"])):
        problems.append("slug must be 1 to 40 of a-z, 0-9 and '-'")
    if not (isinstance(data.get("emoji"), str) and 0 < len(data["emoji"]) <= 4):
        problems.append("emoji must be 1 to 4 characters")
    base = Path(root) / "ports" / "kiro-crew"
    extra = sorted(p.name for p in base.iterdir() if p.name not in KIRO_CREW_FILES) if base.is_dir() else []
    return problems + [f"ports/kiro-crew/{name} would fail the pack install (unexpected file)" for name in extra]


def _kiro_crew_vars(root: Path, text: str) -> list[str]:
    """Both mode blocks set every allowlisted variable with a value the installer accepts. Umber Calm has no light
    variant, so the light block must repeat the dark one."""
    known = _fixture(root, "kirocrew-0.9.0-theme-vars.txt")
    data = json.loads(text)
    problems = [f"top-level keys {sorted(data)} are not ['dark', 'light']"] if set(data) != {"dark", "light"} else []
    for mode in ("dark", "light"):
        block = data.get(mode, {})
        problems += [f"{mode}: unknown Kiro Crew 0.9.0 variable {k!r}" for k in sorted(set(block) - known)]
        problems += [f"{mode}: {k} is not set (Kiro Crew would derive it)" for k in sorted(known - set(block))]
        problems += [f"{mode}: {k} = {v!r} would be rejected by the installer" for k, v in sorted(block.items())
                     if not (isinstance(v, str) and KIRO_CREW_VALUE.fullmatch(v) and not KIRO_CREW_FUNCS.search(v))]
    if data.get("dark") != data.get("light"):
        problems.append("the light block differs from the dark block (Umber Calm is dark only)")
    return problems


def _jetbrains(root: Path, text: str) -> list[str]:
    attributes = ET.fromstring(text).find("attributes")
    mapped = {o.get("name") for o in ([] if attributes is None else attributes)}
    required = _fixture(root, "jetbrains-default-keys.txt") | _fixture(root, "jetbrains-darcula-language-keys.txt")
    return [f"JetBrains key {k} is not mapped (Darcula would show through)" for k in sorted(required - mapped)]


def _base24(root: Path, text: str) -> list[str]:
    problems = [] if 'system: "base24"' in text else ['missing `system: "base24"`']
    slots = re.findall(rf'^  base[0-9A-F]{{2}}: "{HEX}"$', text, re.M)
    return problems + ([] if len(slots) == 24 else [f"{len(slots)} base slots, not 24"])


# Top-level manifest keys and the theme.colors keys the port actually sets (spec §8.1 item 3: Firefox).
FIREFOX_REQUIRED_MANIFEST = ("manifest_version", "name", "version", "theme")
FIREFOX_REQUIRED_THEME_COLORS = (
    "frame", "tab_background_text", "tab_selected", "tab_text", "tab_line", "toolbar", "toolbar_text",
    "toolbar_field", "toolbar_field_text", "toolbar_field_border", "toolbar_field_focus",
    "toolbar_field_border_focus", "popup", "popup_text", "popup_border", "popup_highlight",
    "popup_highlight_text", "sidebar", "sidebar_text", "sidebar_border", "icons", "ntp_background", "ntp_text",
)


def _firefox(root: Path, text: str) -> list[str]:
    data = json.loads(text)
    problems = [f"missing required key {k!r}" for k in FIREFOX_REQUIRED_MANIFEST if k not in data]
    colors = data.get("theme", {}).get("colors", {})
    problems += [f"missing required theme.colors key {k!r}" for k in FIREFOX_REQUIRED_THEME_COLORS if k not in colors]
    known = _fixture(root, "firefox-manifest-theme-colors.txt")
    problems += [f"unknown Firefox theme.colors key {k!r}" for k in sorted(set(colors) - known)]
    return problems


# spec §8.1 item 3: VS Code — the color theme file's own required shape, and package.json's theme contribution.
VSCODE_THEME_REQUIRED = ("name", "type", "colors", "tokenColors")


def _vscode_theme(root: Path, text: str) -> list[str]:
    data = json.loads(text)
    problems = [f"missing required key {k!r}" for k in VSCODE_THEME_REQUIRED if k not in data]
    if "type" in data and data["type"] != "dark":
        problems.append(f'type is {data["type"]!r}, not "dark"')
    if "colors" in data and (not isinstance(data["colors"], dict) or not data["colors"]):
        problems.append("colors must be a non-empty object")
    if "tokenColors" in data and (not isinstance(data["tokenColors"], list) or not data["tokenColors"]):
        problems.append("tokenColors must be a non-empty list")
    return problems


def _vscode_package(root: Path, text: str) -> list[str]:
    data = json.loads(text)
    problems = []
    themes = data.get("contributes", {}).get("themes")
    if not isinstance(themes, list) or not themes:
        problems.append("contributes.themes must be a non-empty list")
    else:
        for i, entry in enumerate(themes):
            problems += [f"contributes.themes[{i}] is missing {k!r}" for k in ("label", "uiTheme", "path")
                        if not isinstance(entry, dict) or k not in entry]
    if not data.get("engines", {}).get("vscode"):
        problems.append("engines.vscode is required")
    return problems


# spec §8.1 item 3: Claude Code — the keys the port's format requires per its template (base and overrides).
CLAUDE_CODE_REQUIRED = ("name", "base", "overrides")


def _claude_code(root: Path, text: str) -> list[str]:
    data = json.loads(text)
    problems = [f"missing required key {k!r}" for k in CLAUDE_CODE_REQUIRED if k not in data]
    if "base" in data and not (isinstance(data["base"], str) and data["base"]):
        problems.append("base must be a non-empty string")
    if "overrides" in data and (not isinstance(data["overrides"], dict) or not data["overrides"]):
        problems.append("overrides must be a non-empty object")
    return problems


# Orca, pinned to stablyai/orca main at fca1d7b: docs/reference/plugin-themes.md, plugin-theme-tokens.md and
# plugin-manifest.md; src/shared/terminal-themes/terminal-custom-themes.ts (TERMINAL_COLOR_KEYS) and
# src/renderer/src/lib/plugin-theme-contrast-rules.ts (which surfaces may be translucent: those checked over a layer).
ORCA_FIXTURE = "orca-main-fca1d7b"
ORCA_FILE_LIMIT = 16 * 1024  # each theme file is at most 16 KiB
ORCA_THEME_TOP = ("schemaVersion", "base", "tokens", "tokenColors")
ORCA_TERMINAL_TOP = ("schemaVersion", "mode", "terminal")
ORCA_TRANSLUCENT = {"--worktree-sidebar-active", "--host-badge", "--chat-user-message", "--chat-inline-code",
                    "--chat-code-block", "--chat-selection", *(f"--diff-{side}-{kind}" for side in ("added", "removed")
                                                               for kind in ("background", "emphasis", "gutter"))}
ORCA_FONT_STYLE = re.compile(r"(?:italic|bold|underline|strikethrough)(?: (?:italic|bold|underline|strikethrough))*|")
ORCA_MANIFEST_TOP = ("$schema", "manifestVersion", "id", "name", "version", "description", "author", "repository",
                     "homepage", "license", "engines", "execution", "contributes")


def _orca_object(text: str, top: tuple[str, ...], what: str) -> tuple[dict | None, list[str]]:
    data, duplicates = _json_with_duplicates(text)
    problems = [f"duplicate key {k!r}" for k in duplicates]
    if len(text.encode("utf-8")) > ORCA_FILE_LIMIT:
        problems.append(f"the {what} is larger than 16 KiB (Orca refuses it)")
    if not isinstance(data, dict):
        return None, problems + [f"the {what} must be a JSON object"]
    problems += [f"unexpected top-level key {k!r} (validate:plugin refuses it)" for k in sorted(set(data) - set(top))]
    problems += [f"missing top-level key {k!r}" for k in top if k not in data]
    return data, problems


def _orca_theme(root: Path, text: str) -> list[str]:
    """An Orca app theme: base dark, every public token set, tokenColors in the shape Orca reads."""
    data, problems = _orca_object(text, ORCA_THEME_TOP, "theme")
    if data is None:
        return problems
    if data.get("schemaVersion", 1) != 1:
        problems.append("schemaVersion must be 1")
    if "base" in data and data["base"] != "dark":
        problems.append(f'base is {data["base"]!r}, not "dark"')
    tokens = data.get("tokens")
    if not isinstance(tokens, dict):
        problems.append("tokens must be a JSON object")
        tokens = {}
    known = _fixture(root, f"{ORCA_FIXTURE}-theme-tokens.txt")
    problems += [f"unknown Orca token {k!r}" for k in sorted(set(tokens) - known)]
    problems += [f"token {k!r} is not set (Orca would derive it)" for k in sorted(known - set(tokens))]
    for k, v in sorted(tokens.items()):
        pattern, label = ((r"#[0-9A-F]{6}(?:[0-9A-F]{2})?", "#RRGGBB or #RRGGBBAA") if k in ORCA_TRANSLUCENT
                          else (HEX, "#RRGGBB"))
        if not (isinstance(v, str) and re.fullmatch(pattern, v)):
            problems.append(f"tokens.{k} is not {label}")
    rules = data.get("tokenColors")
    if not isinstance(rules, list) or not rules:
        return problems + ["tokenColors must be a non-empty list"]
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            problems.append(f"tokenColors[{i}] must be a JSON object")
            continue
        problems += [f"tokenColors[{i}] has unexpected key {k!r}" for k in sorted(set(rule) - {"name", "scope", "settings"})]
        scope = rule.get("scope")
        scopes = [scope] if isinstance(scope, str) else scope
        if not (isinstance(scopes, list) and scopes and all(isinstance(s, str) and s for s in scopes)):
            problems.append(f"tokenColors[{i}] needs a scope or a list of scopes")
        elif any(re.search(r"\s", s) for s in scopes):
            problems.append(f"tokenColors[{i}] has a descendant scope (Orca does not read selectors with spaces)")
        settings = rule.get("settings")
        if not isinstance(settings, dict) or not settings:
            problems.append(f"tokenColors[{i}].settings must be a non-empty object")
            continue
        problems += [f"tokenColors[{i}].settings has unexpected key {k!r}"
                     for k in sorted(set(settings) - {"foreground", "fontStyle"})]
        if "foreground" in settings and not (isinstance(settings["foreground"], str)
                                             and re.fullmatch(HEX, settings["foreground"])):
            problems.append(f"tokenColors[{i}].settings.foreground is not #RRGGBB")
        if "fontStyle" in settings and not (isinstance(settings["fontStyle"], str)
                                            and ORCA_FONT_STYLE.fullmatch(settings["fontStyle"])):
            problems.append(f"tokenColors[{i}].settings.fontStyle is not italic, bold, underline or strikethrough")
    return problems


def _orca_terminal(root: Path, text: str) -> list[str]:
    """An Orca terminal theme: mode dark and every terminal color key set as #RRGGBB."""
    data, problems = _orca_object(text, ORCA_TERMINAL_TOP, "terminal theme")
    if data is None:
        return problems
    if data.get("schemaVersion") != 1:
        problems.append("schemaVersion must be 1")
    if "mode" in data and data["mode"] != "dark":
        problems.append(f'mode is {data["mode"]!r}, not "dark"')
    terminal = data.get("terminal")
    if not isinstance(terminal, dict):
        return problems + ["terminal must be a JSON object"]
    known = _fixture(root, f"{ORCA_FIXTURE}-terminal-keys.txt")
    problems += [f"unknown Orca terminal key {k!r}" for k in sorted(set(terminal) - known)]
    problems += [f"terminal key {k!r} is not set" for k in sorted(known - set(terminal))]
    problems += [f"terminal.{k} is not #RRGGBB" for k, v in sorted(terminal.items())
                 if not (isinstance(v, str) and re.fullmatch(HEX, v))]
    return problems


def _orca_manifest(root: Path, text: str) -> list[str]:
    """orca-plugin.json, manifest format 2: content only, no deprecated publisher, contributions that exist."""
    data, problems = _orca_object(text, ORCA_MANIFEST_TOP, "manifest")
    if data is None:
        return problems
    if data.get("manifestVersion") != 2:
        problems.append("manifestVersion must be 2")
    if "execution" in data and data["execution"] != "data":
        problems.append('execution must be "data" (themes run no code)')
    if "id" in data and not (isinstance(data["id"], str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", data["id"])):
        problems.append("id must be kebab-case")
    engines = data.get("engines")
    if not (isinstance(engines, dict) and isinstance(engines.get("orca"), str)
            and re.fullmatch(r">=\d+\.\d+\.\d+", engines["orca"])):
        problems.append("engines.orca must be >=x.y.z")
    contributes = data.get("contributes")
    if not isinstance(contributes, dict):
        return problems + ["contributes must be a JSON object"]
    problems += [f"unexpected contribution {k!r} (a theme plugin adds themes and terminalThemes only)"
                 for k in sorted(set(contributes) - {"themes", "terminalThemes"})]
    for point, folder in (("themes", "themes"), ("terminalThemes", "terminal")):
        entries = contributes.get(point)
        if not isinstance(entries, list) or not entries:
            problems.append(f"contributes.{point} must be a non-empty list")
            continue
        for i, entry in enumerate(entries):
            if not (isinstance(entry, dict) and set(entry) == {"id", "title", "path"}):
                problems.append(f"contributes.{point}[{i}] must have exactly id, title and path")
                continue
            path = entry["path"]
            if not (isinstance(path, str) and re.fullmatch(rf"{folder}/[a-z0-9-]+\.json", path)):
                problems.append(f"contributes.{point}[{i}].path must be {folder}/<name>.json")
            elif not (Path(root) / "ports/orca" / path).is_file():
                problems.append(f"contributes.{point}[{i}].path names a file the port does not ship")
    return problems


# tmux hex is lowercase: its format expansion reads #D and #F as aliases (templates/tmux/umber-calm.tmux.tmpl).
TMUX_HEX = "#[0-9a-f]{6}"
TMUX_STYLE = rf"(fg|bg)={TMUX_HEX}(,(fg|bg)={TMUX_HEX})?(,bold)?"
I3_LINE = rf"client\.(?:focused|focused_inactive|unfocused|urgent|placeholder) +{HEX}(?: {HEX}){{4}}|client\.background +{HEX}"
FZF_COLORS = rf"--color=[a-z+]+:{HEX}(?:,[a-z+]+:{HEX})*"
DIRCOLORS_CODE = r"[0-9]{1,2}(?:;[0-9]{1,3})*"
EZA_ENTRY = rf' \{{ foreground: "{HEX}"(, is_(?:bold|underline): true)? \}}'
KONSOLE_SECTIONS = ("General", "Background", "BackgroundIntense", "Foreground", "ForegroundIntense",
                    *(f"Color{i}{s}" for i in range(8) for s in ("", "Intense")))

# Output path pattern -> validators. A port task that adds a format with no standard parser adds its row here.
RULES: list[tuple[str, tuple[Validator, ...]]] = [
    ("ports/tmux/*.tmux", (lines(rf'set -g [a-z-]+ "({TMUX_STYLE}|{TMUX_HEX})"'),)),
    ("ports/zellij/*.kdl", (_zellij,)),
    ("ports/konsole/*.colorscheme", (sections(*KONSOLE_SECTIONS, ordered=False),)),
    ("ports/foot/*.ini", (sections("colors-dark"), slots("colors-dark", r"(regular|bright)[0-7]", 16, "[0-9A-F]{6}"))),
    ("ports/xfce4-terminal/*.theme", (entries("Scheme", "ColorPalette", 16, ";", HEX),)),
    ("ports/termux/colors.properties", (slots(None, r"color\d+", 16, HEX),)),
    ("ports/ptyxis/*.palette", (slots("Dark", r"Color\d+", 16, HEX),)),
    ("ports/fuzzel/*.ini", (values("colors", "[0-9A-F]{8}"),)),
    ("ports/kde/*.colors", (sections("General", "Colors:Window", "Colors:View", "Colors:Button", "Colors:Selection",
                                     "Colors:Tooltip", "WM"),)),
    ("ports/qt5ct/*.conf", tuple(entries("ColorScheme", group, 21, ", ", "#[0-9A-F]{8}")
                                 for group in ("active_colors", "inactive_colors", "disabled_colors"))),
    ("ports/dunst/*.dunstrc", (sections("global", "urgency_low", "urgency_normal", "urgency_critical"),)),
    ("ports/eza/theme.yml", (lines(rf"[a-z_]+:({EZA_ENTRY})?|  [a-z_]+:{EZA_ENTRY}"),)),
    ("ports/lazygit/*.yml", (lines(rf'gui:|  theme:|    [A-Za-z]+: \["{HEX}"(, (?:bold|underline|reverse))?\]'),)),
    ("ports/base24/*.yaml", (_base24,)),
    ("ports/zed/themes/*.json", (_zed,)),
    ("ports/yazi/umber-calm.yazi/flavor.toml", (_yazi,)),
    ("ports/herdr/umber-calm.toml", (_herdr,)),
    ("ports/herdr-app/umber-calm.json", (_herdr_app,)),
    ("ports/moshi/umber-calm.json", (_moshi,)),
    ("ports/moshi/umber-calm-import.txt", (_moshi_import,)),
    ("ports/fresh/umber-calm.json", (_fresh,)),
    ("ports/opencode/umber-calm.json", (_opencode,)),
    ("ports/kiro-crew/theme.json", (_kiro_crew_theme,)),
    ("ports/kiro-crew/variables.json", (_kiro_crew_vars,)),
    ("ports/jetbrains/UmberCalm.xml", (_jetbrains,)),
    ("ports/firefox/manifest.json", (_firefox,)),
    ("ports/vscode/themes/*.json", (_vscode_theme,)),
    ("ports/vscode/package.json", (_vscode_package,)),
    ("ports/kiro/package.json", (_vscode_package,)),
    ("ports/claude-code/umber-calm.json", (_claude_code,)),
    ("ports/orca/orca-plugin.json", (_orca_manifest,)),
    ("ports/orca/themes/*.json", (_orca_theme,)),
    ("ports/orca/terminal/*.json", (_orca_terminal,)),
    ("ports/kitty/*.conf", (lines(rf"[a-z0-9_]+ {HEX}"),)),
    ("ports/ghostty/umber-calm", (lines(rf"[a-z-]+ = {HEX}|palette = (?:1[0-5]|[0-9])={HEX}"),
                                  *(_count(rf"palette = {i}={HEX}", 1) for i in range(16)))),
    ("ports/btop/*.theme", (lines(rf'theme\[[a-z0-9_]+\]="{HEX}"'),)),
    ("ports/i3/*.i3", (lines(I3_LINE),)),
    ("ports/sway/*.sway", (lines(I3_LINE),)),
    ("ports/rofi/*.rasi", (_css,)),
    ("ports/*/*.css", (_css,)),
    ("ports/spotify/color.ini", (sections("UmberCalm"), values("UmberCalm", "[0-9A-F]{6}"))),
    ("ports/aider/*.yml", (lines(rf'[a-z-]+: (?:"{HEX}"|true|false|"[a-z0-9-]+")'),)),
    ("ports/delta/*.gitconfig", (lines(r'\[delta "umber-calm"\]|    [a-z-]+ = \S.*'),)),
    ("ports/dircolors/*.dircolors", (lines(rf"TERM \S+|[A-Z_]+ {DIRCOLORS_CODE}|[.*]\S+ {DIRCOLORS_CODE}"),)),
    ("ports/fish/*.theme", (lines(r"fish_(?:pager_)?color_[a-z_]+(?: (?:[0-9A-F]{6}|--[a-z]+(?:=[0-9A-F]{6})?))+"),)),
    ("ports/fzf/*.sh", (lines(rf'export FZF_DEFAULT_OPTS="\$FZF_DEFAULT_OPTS {FZF_COLORS}"'),)),
    ("ports/fzf/*.fish", (lines(rf'set -gx FZF_DEFAULT_OPTS "\$FZF_DEFAULT_OPTS {FZF_COLORS}"'),)),
    ("ports/slack/*.txt", (lambda root, text: [] if re.fullmatch(rf"{HEX}(?:,{HEX}){{7}}\n", text)
                           else ["expected one line of eight comma-separated #RRGGBB colors"],)),
    ("ports/xresources/*.Xresources", (lines(rf"(?:\*\.|XTerm\*)[A-Za-z0-9]+: (?:{HEX}|true|false)", "!"),)),
    ("ports/zathura/*.zathurarc", (lines(rf'set [a-z-]+ (?:"{HEX}"|true|false)'),)),
    ("colors/umber-calm.vim", (_vim,)),
    ("lua/umber-calm/palette.lua", (_lua_table,)),
    ("ports/gnome-terminal/install.sh", (_bash,)),
]


def problems(root: Path, rel: str, text: str) -> list[str]:
    """Structural problems of one generated file, as `structure: <rel>: <problem>` lines."""
    found = []
    for pattern, validators in RULES:
        if not fnmatch.fnmatchcase(rel, pattern):
            continue
        for validate in validators:
            try:
                found += [f"structure: {rel}: {p}" for p in validate(Path(root), text)]
            except (configparser.Error, KeyError, ValueError, ET.ParseError, OSError) as e:
                found.append(f"structure: {rel}: {type(e).__name__}: {e}")
    return found
