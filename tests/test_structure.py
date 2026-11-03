"""check.py runs the structural validators (spec §8.1 item 3) on every generated file."""
import fnmatch, json, os, unittest
from pathlib import Path
from tests.helpers import REPO, tempdir
from umber import checks, outputs, structure

BAD = {
    "ports/herdr-app/umber-calm.json": '{"background": "#201F1D", "background": "#201F1D", "foreground": "#D6C9B6AA", '
                                       '"selection": "#3C3A36", "ansi": ["#2A2826"], "extends": "graphite", '
                                       '"colors": {"hover": "#D6C9B6", "muted": "#938A7B0D", "bogus": "#000000"}}',
    "ports/moshi/umber-calm.json": '{"v": 2, "name": "Umber Calm", "mode": "dim", "colors": {"background": "#201F1D"}}',
    "ports/moshi/umber-calm-import.txt": "moshi-theme:eyJ2IjoxfQ==\n",
    "ports/tmux/umber-calm.tmux": 'set -g status-style "fg=#d6c9b6"\nset-option -g bogus 1\n',
    "ports/zellij/umber-calm.kdl": 'themes {\n    umber-calm {\n        fg "#D6C9B6"\n    }\n',
    "ports/foot/umber-calm.ini": "[colors-dark]\nregular0=201F1D\nregular0=201F1D\n",
    "ports/konsole/Umber Calm.colorscheme": "[General]\nName=x\n",
    "ports/xfce4-terminal/umber-calm.theme": "[Scheme]\nColorPalette=#201F1D;#E08374\n",
    "ports/termux/colors.properties": "color0=#201F1D\n",
    "ports/ptyxis/umber-calm.palette": "[Dark]\nColor0=#201F1D\n",
    "ports/fuzzel/umber-calm.ini": "[colors]\nbackground=201F1D\n",
    "ports/kde/UmberCalm.colors": "[General]\n[WM]\n",
    "ports/qt5ct/umber-calm.conf": "[ColorScheme]\nactive_colors=#FF000000\n",
    "ports/dunst/umber-calm.dunstrc": "[global]\n",
    "ports/eza/theme.yml": "filekinds:\n  normal: { foreground: red }\n",
    "ports/lazygit/umber-calm.yml": "gui:\n  theme:\n    activeBorderColor: [orange]\n",
    "ports/base24/umber-calm.yaml": 'system: "base24"\n  base00: "#201F1D"\n',
    "ports/firefox/manifest.json": '{"manifest_version": 2, "name": "Umber Calm", "theme": {"colors": {}}}',
    "ports/vscode/themes/umber-calm-color-theme.json": '{"name": "Umber Calm", "type": "dark", '
                                                       '"colors": {"editor.background": "#201F1D"}}',
    "ports/vscode/package.json": '{"engines": {"vscode": "^1.95.0"}}',
    "ports/kiro/package.json": '{"contributes": {"themes": [{"label": "Umber Calm"}]}}',
    "ports/herdr/umber-calm.toml": '[theme]\nname = "terminal"\n[theme.custom]\npeach = "orange"\nnot_a_token = "#201F1D"\n',
    "ports/fresh/umber-calm.json": '{"name": "Umber Calm", "extends": "dark", "editor": {"bg": "#201F1D", "bg": [32, 31, 29]}, '
                                   '"syntax": {"keyword": [300, 0, 0], "bogus": [1, 2, 3]}}',
    "ports/claude-code/umber-calm.json": '{"name": "Umber Calm", "base": "dark-ansi"}',
    "ports/kiro-crew/theme.json": '{"formatVersion": 2, "slug": "Umber Calm", "name": "Umber Calm", "level": 1}',
    "ports/kiro-crew/variables.json": '{"dark": {"--bg": "#201F1D", "--text": "url(x)", "--not-a-var": "#000000"}}',
    "ports/kitty/umber-calm.conf": "foreground #D6C9B6\nbackground: #201F1D\n",
    "ports/ghostty/umber-calm": "background = #201F1D\npalette = 0=#2A2826\n",
    "ports/btop/umber-calm.theme": 'theme[main_bg]="#201F1D"\ntheme[main_fg]=#D6C9B6\n',
    "ports/i3/umber-calm.i3": "client.focused #EDA97C #2A2826\n",
    "ports/sway/umber-calm.sway": "client.focused #EDA97C #2A2826 #D6C9B6 #EDA97C #EDA97C\nbar { }\n",
    "ports/rofi/umber-calm.rasi": "* {\n    bg: #201F1D;\n\nwindow { background-color: @bg; }\n",
    "ports/spotify/color.ini": "[UmberCalm]\ntext = #D6C9B6\n",
    "ports/aider/aider.conf.yml": 'dark-mode: true\nuser-input-color: #88B0B4\n',
    "ports/delta/umber-calm.gitconfig": '[delta "umber-calm"]\n    dark = true\nminus-style = x\n',
    "ports/dircolors/umber-calm.dircolors": "DIR 01;34\n.tar red\n",
    "ports/fish/Umber Calm.theme": "fish_color_normal D6C9B6\nset fish_color_command 88B0B4\n",
    "ports/fzf/umber-calm.sh": 'export FZF_DEFAULT_OPTS="$FZF_DEFAULT_OPTS --color=fg:red"\n',
    "ports/fzf/umber-calm.fish": 'set -gx FZF_DEFAULT_OPTS "--color=fg:#D6C9B6"\n',
    "ports/slack/umber-calm.txt": "#1A1917,#2A2826\n",
    "ports/xresources/umber-calm.Xresources": "*.foreground: #D6C9B6\n*.color0 #2A2826\n",
    "ports/zathura/umber-calm.zathurarc": 'set default-bg "#201F1D"\nmap j scroll down\n',
    "ports/css/umber-calm.css": ":root {\n  --umber-bg: #201F1D\n  --x: #000000;\n}\n",
    "ports/gtk/gtk.css": "@define-color accent_color #88B0B4\n",
    "ports/waybar/umber-calm.css": "@define-color bg #201F1D;\nwindow { color: @text; \n",
    "ports/tailwind/umber-calm.css": "@theme {\n  --color-umber-bg #201F1D;\n}\n",
    "ports/vimium/umber-calm.css": "/* unterminated comment\n#vomnibar { background: #2A2826; }\n",
    "ports/obsidian/theme.css": ".theme-dark {\n  --background-primary: #201F1D;\n}}\n",
    "ports/discord/umber-calm.theme.css": ".theme-dark { { --x: #000000; } }\n",
    "colors/umber-calm.vim": 'set background=dark\nhi Normal guifg=#D6C9B6 bogus=1\nif has("x")\n',
    "lua/umber-calm/palette.lua": 'return {\n  colors = { bg = "#201F1D" ,\n}\n',
    "ports/gnome-terminal/install.sh": "#!/usr/bin/env bash\nif true; then\n  echo x\n",
    "ports/sublime/Umber Calm.sublime-color-scheme": '{"rules": [}',
}


class StructureTest(unittest.TestCase):
    def test_every_rule_matches_a_generated_file(self):
        manifest = outputs.read_manifest(REPO)
        for pattern, _ in structure.RULES:
            self.assertTrue(any(fnmatch.fnmatchcase(rel, pattern) for rel in manifest), f"no generated file matches {pattern}")

    def test_generated_files_pass(self):
        found = []
        for rel in sorted(outputs.read_manifest(REPO)):
            try:
                text = (REPO / rel).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            found += structure.problems(REPO, rel, text)
        self.assertEqual(found, [])

    def test_every_generated_configuration_file_has_a_validator(self):
        """M7: every emitted configuration format is at least checked for well-formedness."""
        unchecked = []
        for rel in sorted(outputs.read_manifest(REPO)):
            if rel.endswith(".md") or rel.rsplit("/", 1)[-1].startswith("LICENSE"):
                continue  # documentation and license text, not configuration
            if rel.lower().endswith(checks.PARSED_SUFFIXES):
                continue
            if not any(fnmatch.fnmatchcase(rel, pattern) for pattern, _ in structure.RULES):
                unchecked.append(rel)
        self.assertEqual(unchecked, [])

    def test_herdr_app_validator_names_each_defect(self):
        rel = "ports/herdr-app/umber-calm.json"
        top = {"background", "terminal_foreground", "selection", "cursor", *(f"ansi{i}" for i in range(16))}
        known = set((REPO / "tests/fixtures/herdr-app-0.1.12-theme-keys.txt").read_text(encoding="utf-8").split())
        good = {"background": "#201F1D", "foreground": "#D6C9B6", "selection": "#3C3A36", "cursor": "#EDA97C",
                "ansi": ["#201F1D"] * 16,
                "colors": {k: "#D6C9B617" if k in {"hover", "selected"} else "#201F1D" for k in sorted(known - top)}}
        self.assertEqual(structure.problems(REPO, rel, json.dumps(good)), [])
        cases = [
            ("[]", "the theme must be a JSON object"),
            ("null", "the theme must be a JSON object"),
            (json.dumps(good).replace('"background":', '"background": "#201F1D", "background":', 1),
             "duplicate key 'background'"),
            (json.dumps(good).replace('"hover":', '"hover": "#D6C9B617", "hover":', 1), "duplicate key 'hover'"),
            (json.dumps({**good, "extends": "graphite"}), "unexpected top-level key 'extends'"),
            (json.dumps({k: v for k, v in good.items() if k != "cursor"}), "missing top-level key 'cursor'"),
            (json.dumps({**good, "foreground": "#D6C9B6AA"}), "foreground is not #RRGGBB"),
            (json.dumps({**good, "background": 42}), "background is not #RRGGBB"),
            (json.dumps({**good, "ansi": ["#201F1D"]}), "ansi must have exactly 16 entries"),
            (json.dumps({**good, "ansi": {}}), "ansi must be a list"),
            (json.dumps({**good, "ansi": ["#201F1D"] * 15 + ["#201F1DAA"]}), "ansi[15] is not #RRGGBB"),
            (json.dumps({**good, "ansi": ["#201F1D"] * 15 + [None]}), "ansi[15] is not #RRGGBB"),
            (json.dumps({**good, "colors": []}), "colors must be a JSON object"),
            (json.dumps({**good, "colors": {**good["colors"], "bogus": "#000000"}}), "unknown Herdr color 'bogus'"),
            (json.dumps({**good, "colors": {k: v for k, v in good["colors"].items() if k != "muted"}}),
             "color 'muted' is not set (Herdr would derive it)"),
            (json.dumps({**good, "colors": {**good["colors"], "muted": "#938A7B0D"}}), "colors.muted is not #RRGGBB"),
            (json.dumps({**good, "colors": {**good["colors"], "hover": "#D6C9B6"}}), "colors.hover is not #RRGGBBAA"),
            (json.dumps({**good, "colors": {**good["colors"], "selected": False}}), "colors.selected is not #RRGGBBAA"),
        ]
        for text, expected in cases:
            with self.subTest(expected=expected):
                found = structure.problems(REPO, rel, text)
                self.assertTrue(any(expected in p for p in found), (expected, found))

    def test_moshi_validator_names_each_defect(self):
        """One defect at a time on the generated theme, and the same theme behind the paste string."""
        rel = "ports/moshi/umber-calm.json"
        good = json.loads((REPO / rel).read_text(encoding="utf-8"))
        self.assertEqual(structure.problems(REPO, rel, json.dumps(good)), [])

        def colors(**changes):
            merged = {**good["colors"], **changes}
            return json.dumps({**good, "colors": {k: v for k, v in merged.items() if v is not None}})
        cases = [
            ("[]", "the theme must be a JSON object"),
            (json.dumps(good).replace('"v":', '"v": 1, "v":', 1), "duplicate key 'v'"),
            (json.dumps({**good, "v": 2}), "v must be 1"),
            (json.dumps({**good, "v": True}), "v must be 1"),
            (json.dumps({**good, "v": 1.0}), "v must be 1"),
            (json.dumps({**good, "name": ""}), "name must be 1 to 40 characters"),
            (json.dumps({**good, "name": "x" * 41}), "name must be 1 to 40 characters"),
            (json.dumps({**good, "mode": "dim"}), "mode must be 'dark' or 'light'"),
            (json.dumps({k: v for k, v in good.items() if k != "mode"}), "missing top-level key 'mode'"),
            (json.dumps({**good, "extra": 1}), "unexpected top-level key 'extra'"),
            (json.dumps({**good, "colors": []}), "colors must be a JSON object"),
            (colors(glow="#ffffff"), "unknown Moshi color 'glow'"),
            (colors(cursor=None), "color 'cursor' is not set (Moshi would derive it)"),
            (colors(background="#201F1D"), "colors.background is not #rrggbb"),
            (colors(red="#e08"), "colors.red is not #rrggbb"),
            (colors(bold="loud"), "colors.bold is not #rrggbb or 'bright'"),
        ]
        for text, expected in cases:
            with self.subTest(expected=expected):
                found = structure.problems(REPO, rel, text)
                self.assertTrue(any(expected in p for p in found), (expected, found))
        self.assertEqual(structure.problems(REPO, rel, colors(bold="bright")), [])

        paste = "ports/moshi/umber-calm-import.txt"
        self.assertEqual(structure.problems(REPO, paste, (REPO / paste).read_text(encoding="utf-8")), [])
        for text, expected in [
            ("moshi-theme:eyJ2IjoxfQ==\n", "one line: moshi-theme: and base64url without padding"),
            ("eyJ2IjoxfQ\n", "one line: moshi-theme: and base64url without padding"),
            ("moshi-theme:eyJ2IjoxfQ\nmore\n", "one line: moshi-theme: and base64url without padding"),
            ("moshi-theme:e\n", "the payload is not base64url of UTF-8 JSON"),
            ("moshi-theme:eyJ2IjoxfQ\n", "payload: missing top-level key 'name'"),
        ]:
            with self.subTest(expected=expected):
                found = structure.problems(REPO, paste, text)
                self.assertTrue(any(expected in p for p in found), (expected, found))

    def test_fresh_wrong_containers_are_reported_not_raised(self):
        for text in ("[]", "null", '{"name": "Umber Calm", "editor": 42}', '{"name": "Umber Calm", "ui": []}'):
            self.assertTrue(structure.problems(REPO, "ports/fresh/umber-calm.json", text), text)

    def test_fresh_validator_names_each_defect(self):
        """One defect at a time on the generated theme: each safeguard reports on its own."""
        rel = "ports/fresh/umber-calm.json"
        good = (REPO / rel).read_text(encoding="utf-8")
        self.assertEqual(structure.problems(REPO, rel, good), [])

        def mutated(section, key, value):
            data = json.loads(good)
            data[section][key] = value
            return json.dumps(data)
        cases = [
            (good.replace('"fg": [', '"fg": [1, 2, 3], "fg": [', 1), "duplicate key 'fg'"),
            (mutated("editor", "bg", "#201F1D"), "editor.bg is not [r, g, b]"),
            (mutated("syntax", "keyword", "Red"), "syntax.keyword is not [r, g, b]"),
            (mutated("editor", "bg", "Default"), "editor.bg is not [r, g, b]"),
            (mutated("ui", "semantic_highlight_bg", {"color": "Default", "modifier": ["underlined"]}),
             "ui.semantic_highlight_bg is not [r, g, b]"),  # Color::Reset: the terminal's own background
            (mutated("editor", "bg", [256, 0, 0]), "editor.bg is not [r, g, b]"),
            (mutated("editor", "bg", [True, 0, 0]), "editor.bg is not [r, g, b]"),
            (mutated("syntax", "comment", {"color": [147, 138, 123], "modifier": ["blink"]}), "syntax.comment must be {color, modifier}"),
            (mutated("syntax", "comment", {"color": [147, 138, 123], "bold": True}), "syntax.comment must be {color, modifier}"),
            (mutated("editor", "bracket_rainbow_match_modifier", "bold"), "editor.bracket_rainbow_match_modifier must be a list"),
            (mutated("editor", "not_a_key", [1, 2, 3]), "unknown Fresh 0.5.4 theme key 'editor.not_a_key'"),
            (json.dumps({**json.loads(good), "extends": "dark"}), "the port is standalone: no extends"),
        ]
        dropped = json.loads(good)
        del dropped["ui"]["menu_bg"]
        cases.append((json.dumps(dropped), "Fresh theme key 'ui.menu_bg' is not set"))
        for text, expected in cases:
            found = structure.problems(REPO, rel, text)
            self.assertTrue(any(expected in p for p in found), (expected, found))

    def test_bad_shapes_are_reported(self):
        self.assertEqual({p for p, _ in structure.RULES} - {p for p, _ in structure.RULES
                                                           if any(fnmatch.fnmatchcase(rel, p) for rel in BAD)},
                         {"ports/zed/themes/*.json", "ports/yazi/umber-calm.yazi/flavor.toml", "ports/jetbrains/UmberCalm.xml"})
        for rel, text in BAD.items():
            if rel.endswith(".sh") and os.name == "nt":
                continue  # `bash -n` is skipped on Windows by design (structure._bash); macOS and Linux check it
            found = structure.problems(REPO, rel, text) or checks._format_problems_text(rel, text)
            self.assertTrue(found, rel)
            self.assertTrue(all(p.startswith((f"structure: {rel}: ", f"format: {rel} ")) for p in found), found)

    def test_app_schemas_use_the_committed_key_lists(self):
        zed = '{"themes": [{"style": {"background": "#201F1D", "not.a.zed.key": "#201F1D", "syntax": {}}}]}'
        self.assertEqual(structure.problems(REPO, "ports/zed/themes/umber-calm.json", zed),
                         ["structure: ports/zed/themes/umber-calm.json: unknown Zed style key 'not.a.zed.key'"])
        yazi = '[mgr]\nnot_a_yazi_key = { fg = "#201F1D" }\n'
        self.assertEqual(structure.problems(REPO, "ports/yazi/umber-calm.yazi/flavor.toml", yazi),
                         ["structure: ports/yazi/umber-calm.yazi/flavor.toml: unknown yazi 25.5.28 theme key 'mgr.not_a_yazi_key'"])
        jb = '<scheme><attributes><option name="DEFAULT_KEYWORD"/></attributes></scheme>'
        found = structure.problems(REPO, "ports/jetbrains/UmberCalm.xml", jb)
        self.assertIn("structure: ports/jetbrains/UmberCalm.xml: JetBrains key DEFAULT_STRING is not mapped "
                      "(Darcula would show through)", found)
        self.assertIn("structure: ports/jetbrains/UmberCalm.xml: JetBrains key PY.KEYWORD_ARGUMENT is not mapped "
                      "(Darcula would show through)", found)
        firefox = ('{"manifest_version": 2, "name": "Umber Calm", "version": "1", "theme": {"colors": {'
                  '"frame": "#000000", "tab_background_text": "#000000", "tab_selected": "#000000", '
                  '"tab_text": "#000000", "tab_line": "#000000", "toolbar": "#000000", "toolbar_text": "#000000", '
                  '"toolbar_field": "#000000", "toolbar_field_text": "#000000", "toolbar_field_border": "#000000", '
                  '"toolbar_field_focus": "#000000", "toolbar_field_border_focus": "#000000", "popup": "#000000", '
                  '"popup_text": "#000000", "popup_border": "#000000", "popup_highlight": "#000000", '
                  '"popup_highlight_text": "#000000", "sidebar": "#000000", "sidebar_text": "#000000", '
                  '"sidebar_border": "#000000", "icons": "#000000", "ntp_background": "#000000", '
                  '"ntp_text": "#000000", "not_a_firefox_key": "#000000"}}}')
        self.assertEqual(structure.problems(REPO, "ports/firefox/manifest.json", firefox),
                         ["structure: ports/firefox/manifest.json: unknown Firefox theme.colors key 'not_a_firefox_key'"])

    def test_check_runs_the_validators(self):
        with tempdir() as d:
            root = Path(d)
            (root / "ports/tmux").mkdir(parents=True)
            (root / "ports/tmux/umber-calm.tmux").write_text("set-option -g bogus 1\n", encoding="utf-8")
            [problem] = checks._format_problems(root, "ports/tmux/umber-calm.tmux")
            self.assertTrue(problem.startswith("structure: ports/tmux/umber-calm.tmux: line 1 does not match"), problem)

if __name__ == "__main__":
    unittest.main()
