import json, re, struct, unittest, zlib
from pathlib import Path
from urllib.parse import quote
from tests.helpers import REPO, load_real_palette, tempdir
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

    def test_amber_names_only_what_every_editor_shows(self):
        # VS Code 1.143 hides the active tab's top border, so the page names the cursor and focus, not the tab.
        for text in self.pages().values():
            self.assertIn("Amber only marks where you are: the cursor and whatever has focus.", text)
            self.assertNotIn("active tab", text)

    def test_github_anchors_name_readme_headings(self):
        # GitHub's anchor for "## Ports" is "#ports"; a renamed heading would leave the page linking nowhere.
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        headings = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in re.findall(r"^## (.+)$", readme, re.M)}
        for pid, text in self.pages().items():
            anchors = set(re.findall(re.escape(P.meta["homepage"]) + r"#([\w-]+)", text))
            self.assertEqual(anchors, {"palette", "ports"}, pid)
            self.assertLessEqual(anchors, headings, pid)

    def test_registry_links_use_the_published_extension_names(self):
        # The vscode.dev and Open VSX links are typed in the page; the IDs come from the rendered package.json files.
        vs, kiro = (json.loads((REPO / f"ports/{pid}/package.json").read_text(encoding="utf-8"))
                    for pid in ("vscode", "kiro"))
        label = vs["contributes"]["themes"][0]["label"]
        text = self.pages()["vscode"]
        self.assertIn(f"https://vscode.dev/theme/{vs['publisher']}.{vs['name']}/{quote(label)})", text)
        self.assertIn(f"https://open-vsx.org/extension/{kiro['publisher']}/{kiro['name']})", text)

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

class ManifestTemplateTest(unittest.TestCase):
    def test_package_json_listing_fields(self):
        home = P.meta["homepage"]
        for pid, extra in (("vscode", set()), ("kiro", {"kiro"})):
            pkg = json.loads((REPO / f"ports/{pid}/package.json").read_text(encoding="utf-8"))
            self.assertEqual(pkg["publisher"], marketplace.PUBLISHER)
            self.assertIn("theme", pkg["description"].lower())
            self.assertLessEqual(len(pkg["keywords"]), 30)
            self.assertLessEqual(extra, set(pkg["keywords"]))
            self.assertFalse([k for k in pkg["keywords"] if re.search(r"eye|strain|health|fatigue|headache", k)])
            self.assertEqual(pkg["icon"], "icon.png")
            self.assertEqual(pkg["galleryBanner"], {"color": P.resolve("ui.bg"), "theme": "dark"})
            self.assertEqual((pkg["homepage"], pkg["bugs"], pkg["qna"]), (home, {"url": f"{home}/issues"}, f"{home}/issues"))

    def test_install_lines_point_to_the_registries(self):
        ports = {p.id: p for p in PORTS}
        self.assertIn("VS Code Marketplace", ports["vscode"].install)
        self.assertIn("Open VSX", ports["kiro"].install)
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"https://marketplace.visualstudio.com/items?itemName={marketplace.PUBLISHER}.umber-calm", readme)

def png(width, height) -> bytes:
    """A PNG signature and IHDR chunk: all the image check reads."""
    ihdr = b"IHDR" + struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + ihdr + struct.pack(">I", zlib.crc32(ihdr))

class ImageCheckTest(unittest.TestCase):
    """A temp repo whose vscode page links icon.png, with the icon's SVG source next to it."""
    def setUp(self):
        self.tmp = tempdir()
        self.root = Path(self.tmp.name)
        (self.root / "docs/marketplace").mkdir(parents=True)
        (self.root / "docs/marketplace/vscode.md").write_text(f'<img src="{BASE}icon.png">\n', encoding="utf-8")
        (self.root / "docs/marketplace/icon.svg").write_text("<svg/>\n", encoding="utf-8")
        self.images = self.root / "assets/marketplace"

    def tearDown(self):
        self.tmp.cleanup()

    def add_png(self, name="icon", data=None):
        self.images.mkdir(parents=True, exist_ok=True)
        (self.images / f"{name}.png").write_bytes(png(256, 256) if data is None else data)

    def record(self):
        sources = {"icon": marketplace.source_digest(self.root, "icon")}
        (self.root / marketplace.SOURCES).write_text(json.dumps(sources, indent=2, sort_keys=True) + "\n",
                                                     encoding="utf-8")

    def test_missing_png_is_reported(self):
        self.assertEqual(marketplace.image_problems(self.root),
            ["marketplace: docs/marketplace/vscode.md links assets/marketplace/icon.png, which does not exist"])

    def test_png_without_a_recorded_source_is_reported(self):
        self.add_png()
        self.assertEqual(marketplace.image_problems(self.root),
            ["marketplace: assets/marketplace/icon.png has no entry in assets/marketplace/sources.json"])

    def test_stale_source_is_reported(self):
        self.add_png()
        self.record()
        (self.root / "docs/marketplace/icon.svg").write_text("<svg><rect/></svg>\n", encoding="utf-8")
        self.assertEqual(marketplace.image_problems(self.root),
            ["marketplace: assets/marketplace/icon.png is stale: docs/marketplace/icon.svg changed since it was made "
             "(run tools/marketplace_images.py)"])

    def test_unexpected_png_is_reported(self):
        self.add_png()
        self.record()
        self.add_png("extra")
        self.assertIn("marketplace: assets/marketplace/extra.png is not a listed marketplace image",
                      marketplace.image_problems(self.root))

    def test_unreadable_sources_file_is_reported(self):
        self.add_png()
        for data in (b"{not json", b"[]", b"\xff\xfe"):
            with self.subTest(data=data):
                (self.root / marketplace.SOURCES).write_bytes(data)
                self.assertIn("marketplace: assets/marketplace/sources.json is not a JSON object of image digests "
                              "(run tools/marketplace_images.py)", marketplace.image_problems(self.root))

    def test_icon_smaller_than_the_marketplace_minimum_is_reported(self):
        self.add_png(data=png(64, 128))
        self.record()
        self.assertEqual(marketplace.image_problems(self.root),
            ["marketplace: assets/marketplace/icon.png must be a PNG of at least 128x128 pixels (it is 64x128)"])

    def test_icon_that_is_not_a_png_is_reported(self):
        self.add_png(data=b"GIF89a\x01\x00\x01\x00")
        self.record()
        self.assertEqual(marketplace.image_problems(self.root),
            ["marketplace: assets/marketplace/icon.png must be a PNG of at least 128x128 pixels (it is not a PNG)"])

    def test_icon_at_the_minimum_size_passes(self):
        self.add_png(data=png(128, 128))
        self.record()
        self.assertEqual(marketplace.image_problems(self.root), [])

    def test_current_images_have_no_problems(self):
        self.add_png()
        self.record()
        self.assertEqual(marketplace.image_problems(self.root), [])

if __name__ == "__main__":
    unittest.main()
