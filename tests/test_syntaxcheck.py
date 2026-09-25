import json, plistlib, unittest
from pathlib import Path
from tests.helpers import tempdir
from umber import registry, syntaxcheck

RED, ORANGE = "#E08374", "#EDA97C"
RESERVED = {"red": RED, "orange": ORANGE}

class SyntaxCheckTest(unittest.TestCase):
    def test_extractors(self):
        vs = json.dumps({"colors": {"editorCursor.foreground": ORANGE},
                         "tokenColors": [{"scope": "keyword", "settings": {"foreground": "#DCC07D"}}],
                         "semanticTokenColors": {"enumMember": "#C9A0C0", "type": {"foreground": "#88C0AE"}}})
        self.assertEqual(syntaxcheck.extract("vscode", vs.encode()), ["#DCC07D", "#C9A0C0", "#88C0AE"])
        sub = json.dumps({"globals": {"caret": ORANGE}, "rules": [{"scope": "string", "foreground": "#A7B56E"}]})
        self.assertEqual(syntaxcheck.extract("sublime", sub.encode()), ["#A7B56E"])
        zed = json.dumps({"themes": [{"style": {"syntax": {"keyword": {"color": "#DCC07D"}}}}]})
        self.assertEqual(syntaxcheck.extract("zed", zed.encode()), ["#DCC07D"])
        helix = ('"keyword" = "syntax_keyword"\n"error" = "red"\n"ui.cursor" = { bg = "orange" }\n'
                 '[palette]\nsyntax_keyword = "#DCC07D"\nred = "#E08374"\norange = "#EDA97C"\n')
        self.assertEqual(syntaxcheck.extract("helix", helix.encode()), ["#DCC07D"])
        tm = plistlib.dumps({"settings": [{"settings": {"caret": ORANGE}},
                                          {"scope": "comment", "settings": {"foreground": "#938A7B"}}]})
        self.assertEqual(syntaxcheck.extract("tmtheme", tm), ["#938A7B"])
        vim = "hi Keyword guifg=#DCC07D\nhi Cursor guifg=#201F1D guibg=#EDA97C\nhi Error guifg=#E08374\n"
        self.assertEqual(syntaxcheck.extract("vim", vim.encode()), ["#DCC07D"])
        self.assertEqual(set(syntaxcheck.EXTRACTORS), set(registry.SYNTAX_FORMATS), "extend both together")

    def test_violations(self):
        with tempdir() as d:
            path = Path(d) / "t.json"
            path.write_text(json.dumps({"tokenColors": [{"scope": "keyword", "settings": {"foreground": RED + "CC"}}]}),
                            encoding="utf-8")
            found = syntaxcheck.violations("vscode", path, RESERVED)
            self.assertEqual(len(found), 1)
            self.assertIn("red", found[0])

class IndirectionTest(unittest.TestCase):
    """M7: an extractor resolves indirection or reports the value as unchecked; it never skips it."""
    def violations(self, fmt: str, text: str) -> list[str]:
        with tempdir() as d:
            path = Path(d) / "theme"
            path.write_text(text, encoding="utf-8")
            return syntaxcheck.violations(fmt, path, RESERVED)

    def test_sublime_variables_are_resolved(self):
        data = {"variables": {"warm": "var(hot)", "hot": RED}, "rules": [{"scope": "keyword", "foreground": "var(warm)"}]}
        self.assertEqual(syntaxcheck.extract("sublime", json.dumps(data).encode()), [RED])
        self.assertTrue(any("red" in v for v in self.violations("sublime", json.dumps(data))))
        data = {"rules": [{"scope": "keyword", "foreground": "var(missing)"}]}
        self.assertTrue(any("unchecked" in v for v in self.violations("sublime", json.dumps(data))))

    def test_helix_name_outside_the_palette_is_unchecked(self):
        found = self.violations("helix", '"keyword" = "crimson"\n[palette]\nsyntax_keyword = "#DCC07D"\n')
        self.assertTrue(any("unchecked" in v and "crimson" in v for v in found), found)

    def test_vim_links_are_followed(self):
        text = "hi ErrorMsg guifg=#E08374\nhi link Keyword ErrorMsg\nhi! link Repeat Keyword\n"
        self.assertEqual(syntaxcheck.extract("vim", text.encode()), [RED, RED])
        self.assertEqual(len([v for v in self.violations("vim", text) if "red" in v]), 2)
        found = self.violations("vim", "hi link Keyword NoSuchGroup\nhi link Label Label2\nhi link Label2 Label\n")
        self.assertEqual(len([v for v in found if "unchecked" in v]), 2, found)

    def test_every_real_syntax_file_resolves(self):
        from tests.helpers import REPO
        for port in registry.load_ports(REPO / "ports.toml"):
            if port.syntax_check:
                path = REPO / port.output_root / port.syntax_check["file"]
                values = syntaxcheck.extract(port.syntax_check["format"], path.read_bytes())
                self.assertTrue(values and all(syntaxcheck.HEX.fullmatch(v) for v in values), port.id)

class MoreExtractors(unittest.TestCase):
    KEYWORD, ERROR = "#DCC07D", "#E08374"

    def test_jetbrains_ignores_diagnostics_search_and_base_text(self):
        xml = ('<scheme><attributes>'
               f'<option name="DEFAULT_KEYWORD"><value><option name="FOREGROUND" value="{self.KEYWORD[1:]}"/></value></option>'
               f'<option name="ERRORS_ATTRIBUTES"><value><option name="EFFECT_COLOR" value="{self.ERROR[1:]}"/></value></option>'
               f'<option name="DEFAULT_INVALID_STRING_ESCAPE"><value><option name="EFFECT_COLOR" value="{self.ERROR[1:]}"/></value></option>'
               '</attributes></scheme>')
        self.assertEqual(syntaxcheck.extract("jetbrains", xml.encode()), [self.KEYWORD])

    def test_jetbrains_reads_language_specific_keys_but_not_diagnostics(self):
        # A language-specific Darcula-override key (e.g. PY.KEYWORD) is a syntax mapping and must be read, even
        # though it is not DEFAULT_*-prefixed; a diagnostics key (ERRORS_ATTRIBUTES) is never a syntax mapping,
        # so its FOREGROUND is ignored even when it is red.
        xml = ('<scheme><attributes>'
               f'<option name="PY.KEYWORD"><value><option name="FOREGROUND" value="{self.ERROR[1:]}"/></value></option>'
               f'<option name="ERRORS_ATTRIBUTES"><value><option name="FOREGROUND" value="{self.ERROR[1:]}"/></value></option>'
               '</attributes></scheme>')
        self.assertEqual(syntaxcheck.extract("jetbrains", xml.encode()), [self.ERROR])

    def test_fish_reads_syntax_variables_only(self):
        text = f"fish_color_keyword {self.KEYWORD[1:]}\nfish_color_error {self.ERROR[1:]}\nfish_color_valid_path --underline\n"
        self.assertEqual(syntaxcheck.extract("fish", text.encode()), [self.KEYWORD])

    def test_obsidian_reads_code_variables(self):
        css = f".theme-dark {{\n  --code-keyword: {self.KEYWORD};\n  --text-error: {self.ERROR};\n}}\n"
        self.assertEqual(syntaxcheck.extract("obsidian", css.encode()), [self.KEYWORD])

    def test_opencode_reads_syntax_and_markdown_keys(self):
        data = json.dumps({"theme": {"syntaxKeyword": self.KEYWORD, "error": self.ERROR}})
        self.assertEqual(syntaxcheck.extract("opencode", data.encode()), [self.KEYWORD])

    def test_tmtheme_ignores_diff_scopes(self):
        tm = plistlib.dumps({"settings": [{"settings": {}}, {"scope": "markup.deleted", "settings": {"foreground": self.ERROR}}]})
        self.assertEqual(syntaxcheck.extract("tmtheme", tm), [])

if __name__ == "__main__":
    unittest.main()
