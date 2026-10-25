import re, unittest
from tests.helpers import REPO, load_real_palette
from umber import checks, docsgen, marketplace, registry

P = load_real_palette()
PORTS = registry.load_ports(REPO / "ports.toml")
SRC = re.compile(r'src="([^"]+)"')
BASE = f"https://raw.githubusercontent.com/ChristianOrrala/umber-calm/v{P.meta['release']}/assets/marketplace/"

class NumbersTest(unittest.TestCase):
    def test_ratio_text_never_overstates(self):
        self.assertEqual(marketplace.ratio_text(5.96), "5.9")
        self.assertEqual(marketplace.ratio_text(6.04), "6")
        self.assertEqual(marketplace.ratio_text(9.31), "9.3")

    def test_numbers_match_the_readme(self):
        n = marketplace.numbers(P, PORTS)
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"Main text at {n['text']}:1", readme)
        self.assertIn(f"accents between {n['accent_min']}:1 and {n['accent_max']}:1", readme)
        self.assertEqual(n["ports"], docsgen.badge_values(P, PORTS)["ports"][1])

class PageTest(unittest.TestCase):
    def pages(self):
        return {pid: marketplace.page(pid, P, PORTS) for pid in marketplace.PAGES}

    def test_images_are_https_png_at_the_release_tag(self):
        for pid, text in self.pages().items():
            urls = SRC.findall(text)
            self.assertTrue(urls, pid)
            for url in urls:
                self.assertTrue(url.startswith(BASE) and url.endswith(".png"), url)
            self.assertNotIn("<svg", text)
            self.assertNotIn(".svg", text)
            self.assertNotIn("data:", text)
            self.assertLessEqual(set(marketplace.image_names(text)), set(marketplace.IMAGES))

    def test_vscode_page_has_the_try_link_and_its_hero(self):
        p = self.pages()
        self.assertIn("https://vscode.dev/theme/ChristianOrrala.umber-calm/Umber%20Calm", p["vscode"])
        self.assertNotIn("vscode.dev", p["kiro"])
        self.assertIn("vscode-hero", marketplace.image_names(p["vscode"]))
        self.assertIn("editor", marketplace.image_names(p["kiro"]))
        self.assertIn("https://open-vsx.org/extension/ChristianOrrala/umber-calm-kiro", p["vscode"])

    def test_pages_state_the_measured_numbers(self):
        n = marketplace.numbers(P, PORTS)
        for text in self.pages().values():
            self.assertIn(f"Body text at {n['text']}:1, accents between {n['accent_min']}:1 and {n['accent_max']}:1", text)
            self.assertIn(f"{n['ports']} ports", text)

    def test_pages_follow_the_wording_rules(self):
        for text in self.pages().values():
            for _, pattern in checks.WORDING_PATTERNS:
                self.assertIsNone(pattern.search(text))
            self.assertEqual(text.lower().count("eyes"), 1)
            self.assertIn("I made Umber Calm for my own eyes.", text)

    def test_unknown_port_is_refused(self):
        with self.assertRaises(ValueError):
            marketplace.page("neovim", P, PORTS)

class SourceSvgTest(unittest.TestCase):
    def test_icon_uses_orange_only_for_the_cursor(self):
        svg = marketplace.icon_svg(P)
        fills = re.findall(r'fill="(#[0-9A-Fa-f]{6})"', svg)
        allowed = {P.colors[c] for c in ("bg", "yellow", "blue", "green", "dim_text", "orange")}
        self.assertLessEqual(set(fills), allowed)
        self.assertEqual(fills.count(P.colors["orange"]), 1)
        self.assertIn('width="256" height="256"', svg)

    def test_palette_strip_names_every_accent(self):
        svg = marketplace.palette_svg(P)
        for name in marketplace.ACCENTS:
            self.assertIn(f">{name}<", svg)
            self.assertIn(P.colors[name], svg)

    def test_plan_is_deterministic_and_in_docsgen(self):
        planned = marketplace.plan(P, PORTS)
        self.assertEqual(set(planned), {*marketplace.PAGES.values(), "docs/marketplace/icon.svg", "docs/marketplace/palette.svg"})
        self.assertEqual(planned, marketplace.plan(P, PORTS))
        docs = docsgen.plan(REPO, P, PORTS)
        for rel, entry in planned.items():
            self.assertEqual(docs[rel], entry)
            self.assertEqual(entry[0], "docs")

if __name__ == "__main__":
    unittest.main()
