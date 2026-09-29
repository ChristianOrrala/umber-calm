"""check.py runs the structural validators (spec §8.1 item 3) on every generated file."""
import fnmatch, unittest
from pathlib import Path
from tests.helpers import REPO, tempdir
from umber import checks, outputs, structure

BAD = {
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
    "ports/claude-code/umber-calm.json": '{"name": "Umber Calm", "base": "dark-ansi"}',
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

    def test_bad_shapes_are_reported(self):
        self.assertEqual({p for p, _ in structure.RULES} - {p for p, _ in structure.RULES
                                                           if any(fnmatch.fnmatchcase(rel, p) for rel in BAD)},
                         {"ports/zed/themes/*.json", "ports/yazi/umber-calm.yazi/flavor.toml", "ports/jetbrains/UmberCalm.xml"})
        for rel, text in BAD.items():
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
