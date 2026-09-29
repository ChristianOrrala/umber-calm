"""Structural validators for generated files that no standard parser checks (spec §8.1 item 3).

`checks._format_problems` runs `problems()` on every generated file. RULES maps an output path pattern
(fnmatch, repository-relative) to validators; each validator takes (root, text) and returns problems. They check
shape — INI sections and palette lengths, KDL and tmux line grammars, the YAML subsets we emit, and app schemas
(keys against committed upstream key lists) — never application behavior, which verification records."""
from __future__ import annotations

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
    """herdr 0.9.1 (src/config/theme.rs, CustomThemeColors): [theme] plus every [theme.custom] token, in hex."""
    known = _fixture(root, "herdr-0.9.1-theme-keys.txt")
    data = tomllib.loads(text)
    theme = data.get("theme", {})
    custom = theme.get("custom", {})
    problems = [f"unexpected top-level table {k!r} (the port only sets [theme])" for k in sorted(set(data) - {"theme"})]
    problems += [f"unknown herdr 0.9.1 theme token {k!r}" for k in sorted(set(custom) - known)]
    problems += [f"herdr theme token {k!r} is not set (the base theme would show through)" for k in sorted(known - set(custom))]
    problems += [f"theme.custom.{k} = {v!r} is not #RRGGBB" for k, v in sorted(custom.items())
                 if not (isinstance(v, str) and re.fullmatch(HEX, v))]
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
    ("ports/jetbrains/UmberCalm.xml", (_jetbrains,)),
    ("ports/firefox/manifest.json", (_firefox,)),
    ("ports/vscode/themes/*.json", (_vscode_theme,)),
    ("ports/vscode/package.json", (_vscode_package,)),
    ("ports/claude-code/umber-calm.json", (_claude_code,)),
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
