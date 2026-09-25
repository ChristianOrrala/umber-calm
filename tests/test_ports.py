import json, plistlib, re, tempfile, tomllib, unittest
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from tests import portformats as pf
from tests.helpers import REPO, load_real_palette
from umber import buildcmd, color, registry

P = load_real_palette()
HEX = r"#[0-9A-F]{6}"

def setUpModule():
    buildcmd.build(REPO)

def out(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")

def lines(rel: str, comment: str) -> list[tuple[int, str]]:
    """Non-empty, non-comment lines with their line numbers, for structural checks."""
    return [(n, line) for n, line in enumerate(out(rel).splitlines(), 1)
            if line.strip() and not line.lstrip().startswith(comment)]

def port(pid: str) -> registry.Port:
    return next(p for p in registry.load_ports(REPO / "ports.toml") if p.id == pid)

def composite(value: str, base: str) -> str:
    """The solid color an app draws for `value` (#RRGGBB or #RRGGBBAA) over `base`."""
    alpha = Fraction(int(value[7:9], 16), 255) if len(value) == 9 else Fraction(1)
    return color.blend(value[:7], base, alpha)

class LaunchTerminalPorts(unittest.TestCase):
    def test_wezterm(self):
        data = tomllib.loads(out("ports/wezterm/umber-calm.toml"))
        colors = data["colors"]
        self.assertEqual(colors["background"], P.colors["bg"])
        self.assertEqual([len(colors["ansi"]), len(colors["brights"])], [8, 8])
        self.assertEqual(colors["brights"][0], P.ansi["bright_black"])
        self.assertEqual(colors["tab_bar"]["active_tab"]["fg_color"], P.colors["orange"])
        self.assertEqual(data["metadata"]["name"], "Umber Calm")
        for value in [v for v in colors.values() if isinstance(v, str)] + colors["ansi"] + colors["brights"]:
            self.assertRegex(value, f"^{HEX}$")

    def test_tmux(self):
        text = out("ports/tmux/umber-calm.tmux")
        self.assertIn(f'set -g pane-active-border-style "fg={P.colors["orange"]}"', text)
        self.assertIn(f'set -g pane-border-style "fg={P.colors["inactive"]}"', text)
        self.assertIn(f'set -g clock-mode-colour "{P.colors["text"]}"', text)
        self.assertNotIn(f'set -g clock-mode-colour "{P.colors["orange"]}"', text)
        style = rf'(fg|bg)={HEX}(,(fg|bg)={HEX})?(,bold)?'
        for n, line in lines("ports/tmux/umber-calm.tmux", "#"):
            self.assertRegex(line, rf'^set -g [a-z-]+ "({style}|{HEX})"$', f"line {n}")

    def test_zellij(self):
        """Zellij 0.45.1 component theme: the focused pane frame is ui.focus (spec §5.2), set explicitly."""
        theme = pf.zellij_components(out("ports/zellij/umber-calm.kdl"))
        self.assertEqual(set(theme), set(pf.ZELLIJ_COMPONENTS))
        for name, values in theme.items():
            keys = pf.ZELLIJ_PLAYERS if name == "multiplayer_user_colors" else pf.ZELLIJ_STYLE_KEYS
            self.assertEqual(list(values), list(keys), name)
            for value in values.values():
                self.assertRegex(value, f"^{HEX}$", name)
        focus = P.resolve("ui.focus")
        self.assertEqual(theme["frame_selected"]["base"], focus)
        self.assertEqual(theme["frame_highlight"]["base"], focus)
        self.assertEqual(theme["ribbon_selected"]["background"], focus)
        self.assertNotEqual(theme["frame_unselected"]["base"], focus)
        uses_focus = {name for name, values in theme.items() if focus in values.values()}
        self.assertEqual(uses_focus, {"frame_selected", "frame_highlight", "ribbon_selected"},
                         "focus marks where the user is, never decoration")
        self.assertEqual(port("zellij").target_version, "0.45.1")

    def test_starship(self):
        data = tomllib.loads(out("ports/starship/umber-calm.toml"))
        pal = data["palettes"]["umber_calm"]
        self.assertEqual(pal["text"], P.colors["text"])
        for value in pal.values():
            self.assertRegex(value, f"^{HEX}$")

class ClaudeCodePort(unittest.TestCase):
    def test_overrides(self):
        data = json.loads(out("ports/claude-code/umber-calm.json"))
        self.assertEqual(data["base"], "dark-ansi")
        o = data["overrides"]
        self.assertEqual(o["composerSidebarBackground"], P.colors["surface"])
        self.assertEqual(set(o), {"userMessageBackground", "userMessageBackgroundHover", "bashMessageBackgroundColor",
                                  "memoryBackgroundColor", "composerSidebarBackground"})
        for value in o.values():
            self.assertRegex(value, f"^{HEX}$")

    def test_target_version_is_an_exact_build(self):
        self.assertRegex(port("claude-code").target_version, r"^\d+\.\d+\.\d+$")

# Backgrounds VS Code draws behind code text, with the minimum contrast for `muted` on each (spec §4.4:
# E1 panels 4.0, E3 highlights 3.0). `text` must reach 4.5 on all of them.
VSCODE_TEXT_BACKGROUNDS = {
    "editor.lineHighlightBackground": 4.0, "editor.selectionBackground": 3.0,
    "editor.inactiveSelectionBackground": 3.0, "editor.selectionHighlightBackground": 3.0,
    "editor.findMatchHighlightBackground": 3.0, "editor.wordHighlightBackground": 3.0,
    "editor.wordHighlightStrongBackground": 3.0, "diffEditor.insertedLineBackground": 3.0,
    "diffEditor.removedLineBackground": 3.0, "editorInlayHint.background": 4.0,
    "peekViewEditor.background": 4.0, "editorHoverWidget.background": 4.0, "editorSuggestWidget.background": 4.0,
}

class VSCodePort(unittest.TestCase):
    def setUp(self):
        self.theme = json.loads(out("ports/vscode/themes/umber-calm-color-theme.json"))
        self.c = self.theme["colors"]

    def test_theme_and_manifest(self):
        c = self.c
        self.assertEqual(c["editor.background"], P.colors["bg"])
        self.assertEqual(c["editor.selectionBackground"], P.colors["overlay"])
        self.assertEqual(c["editorCursor.foreground"], P.colors["orange"])
        keyword = next(t for t in self.theme["tokenColors"] if "keyword" in t["scope"])
        self.assertEqual(keyword["settings"]["foreground"], P.colors["yellow"])
        pkg = json.loads(out("ports/vscode/package.json"))
        self.assertEqual(pkg["version"], P.meta["release"])
        self.assertEqual(pkg["contributes"]["themes"][0]["path"], "./themes/umber-calm-color-theme.json")
        self.assertEqual(pkg["engines"]["vscode"], "^" + port("vscode").min_version)

    def test_current_match_is_solid_with_bg_text(self):
        self.assertEqual(self.c["editor.findMatchBackground"], P.resolve("diag.search"))
        self.assertEqual(self.c["editor.findMatchForeground"], P.colors["bg"])
        self.assertGreaterEqual(color.contrast(P.colors["bg"], P.resolve("diag.search")), 4.5)

    def test_text_backgrounds_are_measured(self):
        bg = self.c["editor.background"]
        for key, muted_min in VSCODE_TEXT_BACKGROUNDS.items():
            drawn = composite(self.c[key], bg)
            self.assertGreaterEqual(color.contrast(P.colors["text"], drawn), 4.5, key)
            self.assertGreaterEqual(color.contrast(P.colors["muted"], drawn), muted_min, key)

    def test_alpha_tints_equal_the_measured_tints(self):
        bg = P.colors["bg"]
        search = color.blend(P.resolve("diag.search"), bg, P.tints["search"])
        self.assertEqual(composite(self.c["editor.findMatchHighlightBackground"], bg), search)
        for key, role in (("diffEditor.insertedLineBackground", "diag.diff_add"),
                          ("diffEditor.removedLineBackground", "diag.diff_delete")):
            self.assertEqual(composite(self.c[key], bg), color.blend(P.resolve(role), bg, P.tints["diff"]), key)

WT_KEYS = {"name", "background", "foreground", "cursorColor", "selectionBackground", "black", "red", "green",
           "yellow", "blue", "purple", "cyan", "white", "brightBlack", "brightRed", "brightGreen", "brightYellow",
           "brightBlue", "brightPurple", "brightCyan", "brightWhite"}
FZF_KEYS = {"fg", "bg", "hl", "fg+", "bg+", "hl+", "info", "prompt", "pointer", "marker", "spinner", "header",
            "border", "gutter"}

class CoreTerminalPorts(unittest.TestCase):
    def test_alacritty(self):
        data = tomllib.loads(out("ports/alacritty/umber-calm.toml"))
        c = data["colors"]
        self.assertEqual(c["primary"]["background"], P.colors["bg"])
        self.assertEqual(c["bright"]["black"], P.ansi["bright_black"])
        self.assertEqual(len(c["normal"]), 8)
        self.assertEqual(len(c["bright"]), 8)
        match, focused = c["search"]["matches"], c["search"]["focused_match"]
        self.assertEqual(match["background"], color.blend(P.resolve("diag.search"), P.colors["bg"], P.tints["search"]))
        self.assertGreaterEqual(color.contrast(focused["foreground"], focused["background"]), 4.5)

    def test_kitty_and_ghostty(self):
        self.assertIn(f"color8 {P.ansi['bright_black']}", out("ports/kitty/umber-calm.conf"))
        for n, line in lines("ports/kitty/umber-calm.conf", "#"):
            self.assertRegex(line, rf"^[a-z0-9_]+ {HEX}$", f"kitty line {n}")
        self.assertIn(f"palette = 8={P.ansi['bright_black']}", out("ports/ghostty/umber-calm"))
        slots = []
        for n, line in lines("ports/ghostty/umber-calm", "#"):
            m = re.fullmatch(rf"([a-z-]+) = (?:(\d+)=)?({HEX})", line)
            self.assertIsNotNone(m, f"ghostty line {n}: {line}")
            if m.group(1) == "palette":
                slots.append(int(m.group(2)))
        self.assertEqual(slots, list(range(16)))

    def test_iterm2_float_channels(self):
        data = plistlib.loads((REPO / "ports/iterm2/Umber Calm.itermcolors").read_bytes())
        bg = data["Background Color"]
        self.assertAlmostEqual(bg["Red Component"], 0x20 / 255, places=5)
        self.assertEqual(sorted(k for k in data if k.startswith("Ansi ")), sorted(f"Ansi {i} Color" for i in range(16)))
        for key, value in data.items():
            self.assertEqual(value["Color Space"], "sRGB", key)
            for channel in ("Red Component", "Green Component", "Blue Component"):
                self.assertTrue(0.0 <= value[channel] <= 1.0, key)

    def test_windows_terminal(self):
        data = json.loads(out("ports/windows-terminal/umber-calm.json"))
        self.assertEqual(set(data), WT_KEYS)
        self.assertEqual(data["purple"], P.ansi["magenta"])
        self.assertEqual(data["brightBlack"], P.ansi["bright_black"])
        for key in WT_KEYS - {"name"}:
            self.assertRegex(data[key], f"^{HEX}$", key)

    def test_xresources(self):
        text = out("ports/xresources/umber-calm.Xresources")
        self.assertIn(f"*.color8: {P.ansi['bright_black']}", text)
        self.assertIn(f"*.highlightColor: {P.resolve('term.selection_bg')}", text)
        self.assertIn("xresources patch", text)
        colors = []
        for n, line in lines("ports/xresources/umber-calm.Xresources", "!"):
            m = re.fullmatch(rf"(\*\.|XTerm\*)([A-Za-z0-9]+): ({HEX}|true)", line)
            self.assertIsNotNone(m, f"Xresources line {n}: {line}")
            if m.group(2).startswith("color"):
                colors.append(int(m.group(2)[5:]))
        self.assertEqual(colors, list(range(16)))

    def test_fzf(self):
        self.assertIn(f"pointer:{P.colors['orange']}", out("ports/fzf/umber-calm.sh"))
        self.assertIn("set -gx FZF_DEFAULT_OPTS", out("ports/fzf/umber-calm.fish"))
        for rel in ("ports/fzf/umber-calm.sh", "ports/fzf/umber-calm.fish"):
            spec = re.search(r"--color=([^\"]+)\"", out(rel)).group(1)
            pairs = dict(item.split(":", 1) for item in spec.split(","))
            self.assertEqual(set(pairs), FZF_KEYS, rel)
            for value in pairs.values():
                self.assertRegex(value, f"^{HEX}$", rel)

HELIX_NON_SYNTAX = ("ui.", "diagnostic", "diff.", "warning", "error", "info", "hint")


class EditorPorts(unittest.TestCase):
    def test_helix_syntax_scopes_use_role_aliases(self):
        data = tomllib.loads(out("ports/helix/umber-calm.toml"))
        pal = data["palette"]
        self.assertEqual(data["keyword"], "syntax_keyword")
        self.assertEqual(pal["syntax_keyword"], P.resolve("syntax.keyword"))
        for key, value in data.items():
            if key == "palette" or key.startswith(HELIX_NON_SYNTAX):
                continue
            fg = value if isinstance(value, str) else value.get("fg")
            if fg:
                self.assertTrue(fg.startswith("syntax_"), f"{key} uses {fg!r}, not a syntax_* alias")
                self.assertIn(fg, pal)
        self.assertEqual(pf.non_hex(pal.values(), pf.HEX6), [])

    def test_helix_selection_sets_foreground(self):
        data = tomllib.loads(out("ports/helix/umber-calm.toml"))
        self.assertEqual(data["ui.selection"], {"fg": "ui_selection_fg", "bg": "ui_selection_bg"})
        self.assertEqual(data["palette"]["ui_selection_fg"], P.resolve("ui.selection_fg"))

    def test_zed_shape_and_schema_keys(self):
        data = json.loads(out("ports/zed/themes/umber-calm.json"))
        self.assertEqual(set(data), {"$schema", "name", "author", "themes"})
        [theme] = data["themes"]
        self.assertEqual(theme["appearance"], "dark")
        style = theme["style"]
        known = pf.keys_in((REPO / "tests/fixtures/zed-theme-v0.2.0-keys.txt").read_text(encoding="utf-8"))
        self.assertEqual(sorted(set(style) - known), [])
        self.assertEqual(sorted({k for v in style["syntax"].values() for k in v} - known), [])
        colors = [v for k, v in style.items() if k not in ("players", "syntax")]
        colors += [v["color"] for v in style["syntax"].values()] + [c for p in style["players"] for c in p.values()]
        self.assertEqual(pf.non_hex(colors), [])
        self.assertEqual(style["syntax"]["keyword"]["color"], P.resolve("syntax.keyword"))
        self.assertIn(f'version = "{P.meta["release"]}"', out("ports/zed/extension.toml"))

    def test_jetbrains_maps_every_default_key(self):
        scheme = ET.fromstring(out("ports/jetbrains/UmberCalm.xml"))
        mapped = {o.get("name") for o in scheme.find("attributes")}
        required = pf.keys_in((REPO / "tests/fixtures/jetbrains-default-keys.txt").read_text(encoding="utf-8"))
        self.assertEqual(sorted(required - mapped), [])
        keyword = scheme.find("attributes/option[@name='DEFAULT_KEYWORD']/value/option[@name='FOREGROUND']")
        self.assertEqual("#" + keyword.get("value"), P.resolve("syntax.keyword"))
        # spec §5.1: documentation tags are the muted comment color, bold (FONT_TYPE 1 = bold, 2 = italic)
        tag = {o.get("name"): o.get("value")
               for o in scheme.find("attributes/option[@name='DEFAULT_DOC_COMMENT_TAG']/value")}
        self.assertEqual(tag, {"FOREGROUND": P.resolve("syntax.comment")[1:], "FONT_TYPE": "1"})

    def test_jetbrains_maps_darcula_language_keys(self):
        attributes = ET.fromstring(out("ports/jetbrains/UmberCalm.xml")).find("attributes")
        mapped = {o.get("name"): o for o in attributes}
        required = pf.keys_in((REPO / "tests/fixtures/jetbrains-darcula-language-keys.txt").read_text(encoding="utf-8"))
        self.assertEqual(sorted(required - set(mapped)), [])
        syntax = {P.resolve(f"syntax.{role}")[1:] for role in P.roles["syntax"]}
        reserved = {P.colors["red"][1:], P.colors["orange"][1:]}
        for name in sorted(required - {"KOTLIN_COROUTINE_DEBUGGER_VALUE"}):  # a debugger value, not syntax
            values = {o.get("name"): o.get("value") for o in mapped[name].find("value")}
            self.assertIn(values.get("FOREGROUND"), syntax, f"{name} must use a syntax role color")
            self.assertNotIn(values["FOREGROUND"], reserved, name)
            self.assertNotIn("BACKGROUND", values, f"{name}: Darcula's background must not survive")
        self.assertEqual(mapped["PY.KEYWORD_ARGUMENT"].find("value/option[@name='FOREGROUND']").get("value"),
                         P.resolve("syntax.variable")[1:])
        readme = out("ports/jetbrains/README.md")
        self.assertIn("## Known limitations", readme)
        self.assertIn("JavaScript and TypeScript", readme)
        self.assertIn("## Install", readme, "the intro keeps the generated install section")

    def test_jetbrains_plugin_and_theme(self):
        theme = json.loads(out("ports/jetbrains/UmberCalm.theme.json"))
        self.assertEqual(theme["editorScheme"], "/UmberCalm.xml")
        plugin = ET.fromstring(out("ports/jetbrains/META-INF/plugin.xml"))
        self.assertEqual(plugin.find("extensions/themeProvider").get("path"), "/UmberCalm.theme.json")
        self.assertEqual(plugin.find("version").text, P.meta["release"])

    def test_jetbrains_min_version_equals_since_build(self):
        build = ET.fromstring(out("ports/jetbrains/META-INF/plugin.xml")).find("idea-version").get("since-build")
        self.assertEqual(f"20{build[:2]}.{build[2:]}", port("jetbrains").min_version)

    def test_sublime(self):
        data = json.loads(out("ports/sublime/Umber Calm.sublime-color-scheme"))
        self.assertEqual(data["globals"]["background"], P.colors["bg"])
        self.assertEqual(data["globals"]["selection_foreground"], P.resolve("ui.selection_fg"))
        self.assertEqual(pf.non_hex(list(data["globals"].values()) + [r["foreground"] for r in data["rules"]]), [])

EZA_LINE = re.compile(r'[a-z_]+:( \{ foreground: "#[0-9A-F]{6}"(, is_(?:bold|underline): true)? \})?'
                      r'|  [a-z_]+: \{ foreground: "#[0-9A-F]{6}"(, is_(?:bold|underline): true)? \}')
EZA_SECTIONS = {"colourful", "filekinds", "perms", "size", "users", "links", "git", "git_repo", "security_context",
                "file_type", "punctuation", "date", "inode", "blocks", "header", "octal", "flags", "symlink_path",
                "control_char", "broken_symlink", "broken_path_overlay", "filenames", "extensions"}
LAZYGIT_LINE = re.compile(r'gui:|  theme:|    [A-Za-z]+: \["#[0-9A-F]{6}"(, (?:bold|underline|reverse))?\]')
LAZYGIT_KEYS = {"activeBorderColor", "inactiveBorderColor", "searchingActiveBorderColor", "optionsTextColor",
                "selectedLineBgColor", "inactiveViewSelectedLineBgColor", "cherryPickedCommitFgColor",
                "cherryPickedCommitBgColor", "markedBaseCommitFgColor", "markedBaseCommitBgColor",
                "unstagedChangesColor", "defaultFgColor"}


class ShellCliPorts(unittest.TestCase):
    def test_fish_uses_roles(self):
        text = out("ports/fish/Umber Calm.theme")
        self.assertIn(f"fish_color_keyword {P.resolve('syntax.keyword')[1:]}", text)
        self.assertIn(f"fish_color_autosuggestion {P.resolve('ui.text_secondary')[1:]}", text)

    def test_bat_tmtheme(self):
        data = plistlib.loads((REPO / "ports/bat/Umber Calm.tmTheme").read_bytes())
        self.assertEqual(data["settings"][0]["settings"]["background"], P.colors["bg"])

    def test_changing_the_bat_theme_expires_delta(self):
        bat = "ports/bat/Umber Calm.tmTheme"
        paths = list(buildcmd.states(REPO)["delta"].inputs)
        self.assertIn(bat, paths, "delta renders syntax through the bat theme, so its verification covers it")
        with tempfile.TemporaryDirectory() as d:
            for rel in paths:
                (Path(d) / rel).parent.mkdir(parents=True, exist_ok=True)
                (Path(d) / rel).write_bytes((REPO / rel).read_bytes())
            before = registry.digest(Path(d), paths)
            (Path(d) / bat).write_bytes((REPO / bat).read_bytes().replace(P.colors["yellow"].encode(), b"#000000"))
            self.assertNotEqual(registry.digest(Path(d), paths), before)

    def test_delta_uses_measured_tints(self):
        text = out("ports/delta/umber-calm.gitconfig")
        self.assertIn('[delta "umber-calm"]', text)
        line = P.resolve("diag.diff_add")
        from umber import color
        self.assertIn(f'plus-style = syntax "{color.blend(line, P.colors["bg"], P.tints["diag"])}"', text)
        self.assertIn(f'plus-emph-style = syntax "{color.blend(line, P.colors["bg"], P.tints["diff"])}"', text)
        self.assertNotIn("0.30", (REPO / "templates/delta/umber-calm.gitconfig.tmpl").read_text(encoding="utf-8"))

    def test_lazygit_and_btop(self):
        text = out("ports/lazygit/umber-calm.yml")
        self.assertEqual(pf.line_problems(text, LAZYGIT_LINE), [])
        self.assertEqual(sorted(set(re.findall(r"^    ([A-Za-z]+):", text, re.M)) - LAZYGIT_KEYS), [])
        self.assertIn(P.resolve("ui.focus"), text)
        self.assertIn(f'theme[main_bg]="{P.colors["bg"]}"', out("ports/btop/umber-calm.theme"))

    def test_eza_shape_and_dircolors(self):
        text = out("ports/eza/theme.yml")
        self.assertEqual(pf.line_problems(text, EZA_LINE), [])
        self.assertEqual(sorted(set(re.findall(r"^([a-z_]+):", text, re.M)) - EZA_SECTIONS), [])
        self.assertIn(f'"{P.colors["blue"]}"', text)
        self.assertIn("DIR 01;34", out("ports/dircolors/umber-calm.dircolors"))

    def test_yazi_keys_exist_in_25_5_28_preset(self):
        data = tomllib.loads(out("ports/yazi/umber-calm.yazi/flavor.toml"))
        known = pf.keys_in((REPO / "tests/fixtures/yazi-25.5.28-theme-keys.txt").read_text(encoding="utf-8"))
        ours = {f"{s}.{k}" for s, t in data.items() if s != "filetype" for k in t}
        ours |= {f"filetype.rules[].{k}" for rule in data["filetype"]["rules"] for k in rule}
        self.assertEqual(sorted(ours - known), [])
        self.assertEqual(data["mgr"]["cwd"]["fg"], P.colors["blue"])
        self.assertEqual(port("yazi").target_version, "25.5.28")

    def test_yazi_flavor_package_files(self):
        flavor = REPO / "ports/yazi/umber-calm.yazi"
        self.assertEqual(sorted(p.name for p in flavor.iterdir()),
                         ["LICENSE", "LICENSE-tmtheme", "README.md", "flavor.toml", "tmtheme.xml"])
        self.assertEqual((flavor / "tmtheme.xml").read_bytes(), (REPO / "ports/bat/Umber Calm.tmTheme").read_bytes())
        self.assertEqual((flavor / "LICENSE").read_bytes(), (REPO / "LICENSE").read_bytes())
        self.assertEqual((flavor / "LICENSE-tmtheme").read_bytes(), (REPO / "LICENSE").read_bytes())
        bat_t = (REPO / "templates/bat/Umber Calm.tmTheme.tmpl").read_text(encoding="utf-8")
        yazi_t = (REPO / "templates/yazi/umber-calm.yazi/tmtheme.xml.tmpl").read_text(encoding="utf-8")
        self.assertEqual(yazi_t, bat_t.replace("{{ meta.template }}", "templates/bat/Umber Calm.tmTheme.tmpl"))

class LinuxTerminalPorts(unittest.TestCase):
    def test_gnome_installer_text(self):
        text = out("ports/gnome-terminal/install.sh")
        self.assertTrue(text.startswith("#!/usr/bin/env bash"))
        self.assertIn('UUID="b6885571-c238-4b0d-8904-5a8531dfdbae"', text)
        self.assertIn(f"'{P.colors['bg']}'", text)
        self.assertNotIn("sed ", text)

    def test_konsole_sections_and_decimal(self):
        cp = pf.ini(out("ports/konsole/Umber Calm.colorscheme"))
        expected = {"General", "Background", "BackgroundIntense", "Foreground", "ForegroundIntense"}
        expected |= {f"Color{i}{s}" for i in range(8) for s in ("", "Intense")}
        self.assertEqual(set(cp.sections()), expected)
        r, g, b = (int(P.colors["bg"][i:i + 2], 16) for i in (1, 3, 5))
        self.assertEqual(cp["Background"]["Color"], f"{r},{g},{b}")
        self.assertIn("inherited", port("konsole").install)

    def test_foot(self):
        cp = pf.ini(out("ports/foot/umber-calm.ini"))
        self.assertEqual(cp.sections(), ["colors-dark"])
        colors = cp["colors-dark"]
        self.assertEqual(colors["background"], P.colors["bg"][1:])
        self.assertEqual(len([k for k in colors if re.fullmatch(r"(regular|bright)[0-7]", k)]), 16)
        self.assertEqual(pf.non_hex(["#" + v for k, v in colors.items() if k != "cursor"], pf.HEX6), [])
        self.assertIn("--check-config", " ".join(port("foot").checklist))
        # [colors-dark] was added in foot 1.26.0 (upstream CHANGELOG); older releases reject the section.
        self.assertEqual(port("foot").target_version, "1.26.0")
        self.assertIn("foot 1.26.0 or newer", port("foot").install)

    def test_xfce_termux_ptyxis(self):
        xfce = pf.ini(out("ports/xfce4-terminal/umber-calm.theme"))["Scheme"]
        self.assertEqual(xfce["ColorBackground"], P.colors["bg"])
        self.assertEqual(len(xfce["ColorPalette"].split(";")), 16)
        termux = pf.ini(out("ports/termux/colors.properties"), sectionless=True)["root"]
        self.assertEqual(termux["color8"], P.ansi["bright_black"])
        self.assertEqual(len([k for k in termux if re.fullmatch(r"color\d+", k)]), 16)
        ptyxis = pf.ini(out("ports/ptyxis/umber-calm.palette"))
        self.assertEqual(ptyxis["Dark"]["Background"], P.colors["bg"])
        self.assertEqual(ptyxis["Dark"]["Cursor"], P.resolve("term.cursor"))
        self.assertEqual(len([k for k in ptyxis["Dark"] if re.fullmatch(r"Color\d+", k)]), 16)

class DesktopPorts(unittest.TestCase):
    def test_window_managers(self):
        self.assertIn(f"client.focused          {P.colors['orange']}", out("ports/i3/umber-calm.i3"))
        self.assertEqual(out("ports/i3/umber-calm.i3").splitlines()[1:], out("ports/sway/umber-calm.sway").splitlines()[1:])

    def test_fuzzel_rrggbbaa(self):
        colors = pf.ini(out("ports/fuzzel/umber-calm.ini"))["colors"]
        self.assertEqual(colors["background"], P.colors["bg"][1:] + "FF")
        self.assertEqual([v for v in colors.values() if not re.fullmatch(r"[0-9A-F]{8}", v)], [])

    def test_kde_sections_and_qt_palette_lengths(self):
        kde = pf.ini(out("ports/kde/UmberCalm.colors"))
        self.assertEqual(kde.sections(), ["General", "Colors:Window", "Colors:View", "Colors:Button",
                                          "Colors:Selection", "Colors:Tooltip", "WM"])
        r, g, b = (int(P.colors["bg"][i:i + 2], 16) for i in (1, 3, 5))
        self.assertEqual(kde["Colors:Window"]["BackgroundNormal"], f"{r},{g},{b}")
        qt = pf.ini(out("ports/qt5ct/umber-calm.conf"))["ColorScheme"]
        for group in ("active_colors", "inactive_colors", "disabled_colors"):
            entries = qt[group].split(", ")
            self.assertEqual(len(entries), 21, group)
            self.assertEqual(pf.non_hex(entries, re.compile(r"#[0-9A-F]{8}")), [])
        self.assertIn("#FF" + P.colors["bg"][1:], qt["active_colors"])

    def test_gtk_rofi_dunst_waybar_zathura(self):
        self.assertIn(f"@define-color window_bg_color {P.colors['bg']};", out("ports/gtk/gtk.css"))
        self.assertIn(f"bg: {P.colors['bg']};", out("ports/rofi/umber-calm.rasi"))
        dunst = pf.ini(out("ports/dunst/umber-calm.dunstrc"))
        self.assertEqual(dunst.sections(), ["global", "urgency_low", "urgency_normal", "urgency_critical"])
        self.assertEqual(dunst["urgency_critical"]["frame_color"], f'"{P.colors["red"]}"')
        self.assertIn(f"@define-color focus {P.colors['orange']};", out("ports/waybar/umber-calm.css"))
        zathura = out("ports/zathura/umber-calm.zathurarc")
        self.assertIn(f'set default-bg "{P.colors["bg"]}"', zathura)
        self.assertNotIn("0.4", (REPO / "templates/zathura/umber-calm.zathurarc.tmpl").read_text(encoding="utf-8"))

    def test_base24_has_24_slots(self):
        text = out("ports/base24/umber-calm.yaml")
        self.assertIn('system: "base24"', text)
        self.assertEqual(len(re.findall(r'^  base[0-9A-F]{2}: "#[0-9A-F]{6}"$', text, re.M)), 24)
        self.assertIn(f'base00: "{P.colors["bg"]}"', text)

FIREFOX_THEME_COLORS = {
    "frame", "frame_inactive", "tab_background_text", "tab_selected", "tab_text", "tab_line", "tab_loading",
    "tab_background_separator", "toolbar", "toolbar_text", "toolbar_field", "toolbar_field_text",
    "toolbar_field_border", "toolbar_field_focus", "toolbar_field_text_focus", "toolbar_field_border_focus",
    "toolbar_field_highlight", "toolbar_field_highlight_text", "toolbar_field_separator", "toolbar_top_separator",
    "toolbar_bottom_separator", "toolbar_vertical_separator", "popup", "popup_text", "popup_border",
    "popup_highlight", "popup_highlight_text", "sidebar", "sidebar_text", "sidebar_border", "sidebar_highlight",
    "sidebar_highlight_text", "icons", "icons_attention", "ntp_background", "ntp_card_background", "ntp_text",
    "button_background_hover", "button_background_active", "bookmark_text"}  # MDN manifest.json/theme, theme.colors
RISK_PINS = {"discord": r"Vencord (v?\d+\.\d+\.\d+|[0-9a-f]{7,40}) on Discord Stable \d+",
             "spotify": r"Spicetify \d+\.\d+\.\d+ on Spotify \d+(\.[0-9A-Za-z]+)+"}


class AppPorts(unittest.TestCase):
    def test_slack_legacy_string(self):
        parts = out("ports/slack/umber-calm.txt").strip().split(",")
        self.assertEqual(len(parts), 8)
        self.assertEqual(pf.non_hex(parts, pf.HEX6), [])
        self.assertIn("Import theme", port("slack").install)

    def test_firefox_manifest(self):
        data = json.loads(out("ports/firefox/manifest.json"))
        self.assertEqual(data["manifest_version"], 2)
        self.assertEqual(set(data), {"manifest_version", "name", "version", "description", "browser_specific_settings", "theme"})
        self.assertEqual(sorted(set(data["theme"]["colors"]) - FIREFOX_THEME_COLORS), [])
        self.assertEqual(pf.non_hex(data["theme"]["colors"].values()), [])
        self.assertEqual(data["theme"]["colors"]["tab_line"], P.colors["orange"])

    def test_obsidian_manifest_and_min_version(self):
        data = json.loads(out("ports/obsidian/manifest.json"))
        self.assertEqual(data["version"], P.meta["release"])
        self.assertEqual(data["minAppVersion"], port("obsidian").min_version)
        self.assertIn(f"--background-primary: {P.colors['bg']};", out("ports/obsidian/theme.css"))

    def test_other_json_files_parse(self):
        for rel in ("ports/vivaldi/settings.json", "ports/opencode/umber-calm.json"):
            json.loads(out(rel))

    def test_css_family(self):
        self.assertIn(f"--color-umber-bg: {P.colors['bg']};", out("ports/tailwind/umber-calm.css"))
        self.assertIn(f"--umber-bg: {P.colors['bg']};", out("ports/css/umber-calm.css"))
        self.assertIn("@name Umber Calm", out("ports/discord/umber-calm.theme.css"))

    def test_spotify_and_aider(self):
        self.assertIn(f"main               = {P.colors['bg'][1:]}", out("ports/spotify/color.ini"))
        self.assertIn(f'tool-error-color: "{P.colors["red"]}"', out("ports/aider/aider.conf.yml"))

    def test_risk_ports_are_pinned_or_candidates(self):
        for pid, pattern in RISK_PINS.items():
            p = port(pid)
            self.assertTrue(p.risk, pid)
            if p.format_confirmed:
                self.assertRegex(p.target_version, f"^{pattern}$")
            else:
                self.assertTrue(p.target_version.startswith("unpinned"), pid)

if __name__ == "__main__":
    unittest.main()
