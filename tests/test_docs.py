import re, unittest
from tests.helpers import REPO, load_real_palette
from umber import checks

P = load_real_palette()
GUIDE = (REPO / "docs/style-guide.md").read_text(encoding="utf-8")

class StyleGuideTest(unittest.TestCase):
    def test_color_table_matches_the_palette(self):
        rows = dict(re.findall(r"^\| `([a-z_]+)` \| `(#[0-9A-F]{6})` \|", GUIDE, re.M))
        self.assertEqual(rows, P.colors)

    def test_role_tables_match_the_palette(self):
        for contract, roles in P.roles.items():
            for role, name in roles.items():
                self.assertIn(f"| {role} | `{name}` |", GUIDE, f"{contract}.{role}")

    def test_ansi_table_matches_the_palette(self):
        for slot in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"):
            self.assertIn(f"| {slot} | `{P.ansi[slot]}` | `{P.ansi['bright_' + slot]}` |", GUIDE)

class WordingTest(unittest.TestCase):
    def test_docs_follow_the_wording_rules(self):
        for rel in ("docs/design.md", "docs/style-guide.md", "README.md"):
            text = (REPO / rel).read_text(encoding="utf-8")
            for label, pattern in checks.WORDING_PATTERNS:
                self.assertIsNone(pattern.search(text), f"{rel}: {label}")
        self.assertIn("I made Umber Calm for my own eyes.", (REPO / "docs/design.md").read_text(encoding="utf-8"))

class PublicDocsTest(unittest.TestCase):
    def test_contributing_has_the_release_order(self):
        text = (REPO / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertIn("## Release process", text)
        section = text[text.index("## Release process"):]
        steps = ["**Verify**", "build.py digest", "**Mark**", "build.py mark", "**Build**", "**Package**",
                 "tools/package.py", "**Commit**", "**Run the release gate**", "release_gate.py --tag", "**Push**",
                 "**Tag**"]
        positions = [section.find(step) for step in steps]
        self.assertNotIn(-1, positions, dict(zip(steps, positions)))
        self.assertEqual(positions, sorted(positions), "release steps are in order")

    def test_name_check_names_its_method(self):
        self.assertNotIn("(manual)", (REPO / "docs/decisions/name.md").read_text(encoding="utf-8"))

    def test_public_docs_do_not_cite_the_private_design_spec(self):
        import re
        for path in [REPO / "README.md", REPO / "CONTRIBUTING.md", REPO / "CHANGELOG.md", *sorted((REPO / "docs").rglob("*.md"))]:
            self.assertIsNone(re.search(r"\bspec(?:ification)?\s*§|§\s*\d", path.read_text(encoding="utf-8")),
                              path.relative_to(REPO).as_posix())

if __name__ == "__main__":
    unittest.main()
