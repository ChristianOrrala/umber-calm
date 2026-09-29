import json, re, unittest
import xml.etree.ElementTree as ET
from tests.helpers import REPO, load_real_palette
from umber import buildcmd, color, cvd, docsgen, outputs, registry, render_svg

P = load_real_palette()
FIXTURE = json.loads((REPO / docsgen.FIXTURE).read_text(encoding="utf-8"))
LINES = [line for f in FIXTURE["files"] for line in f["lines"]]
SPANS = [span for line in LINES for span in line["spans"]]

class RenderTest(unittest.TestCase):
    def test_fixture_covers_every_role_state_and_severity(self):
        self.assertEqual({s[0] for s in SPANS if s[0]}, set(P.roles["syntax"]))
        self.assertEqual({s[2] for s in SPANS if len(s) > 2}, set(render_svg.SPAN_STATES))
        self.assertEqual({line["state"] for line in LINES if "state" in line}, set(render_svg.LINE_STATES))
        self.assertEqual({line["diagnostic"]["severity"] for line in LINES if "diagnostic" in line},
                         set(render_svg.SEVERITIES))

    def test_screenshot_sources_are_the_fixture_text(self):
        for f in FIXTURE["files"]:
            text = "".join("".join(s[1] for s in line["spans"]) + "\n" for line in f["lines"])
            self.assertEqual((REPO / "tests/fixtures" / f["name"]).read_text(encoding="utf-8"), text, f["name"])

    def test_deterministic_valid_and_uses_measured_states(self):
        svg = render_svg.render(FIXTURE, P)
        self.assertEqual(svg, render_svg.render(FIXTURE, P))
        ET.fromstring(svg)
        search_tint = render_svg.color.blend(P.resolve("diag.search"), P.colors["bg"], P.tints["search"])
        for fill in (P.resolve("diag.search"), search_tint, P.resolve("ui.selection_bg")):
            self.assertIn(f'fill="{fill}"', svg)

    def test_simulated_renders(self):
        gray = render_svg.render(FIXTURE, P, lambda hx: cvd.simulate(hx, "grayscale"))
        for hx in set(re.findall(r'fill="(#[0-9A-F]{6})"', gray)):
            self.assertTrue(hx[1:3] == hx[3:5] == hx[5:7], hx)
        deut = render_svg.render(FIXTURE, P, lambda hx: cvd.simulate(hx, "deuteranopia"))
        self.assertNotIn(f'fill="{P.colors["green"]}"', deut)

    def test_render_background_has_rounded_corners(self):
        svg = render_svg.render(FIXTURE, P)
        rect = ET.fromstring(svg).find("{http://www.w3.org/2000/svg}rect")
        self.assertEqual(rect.get("fill"), P.resolve("ui.bg"))
        self.assertGreater(float(rect.get("rx")), 0)

    def test_build_writes_the_generated_docs(self):
        buildcmd.build(REPO)
        manifest = outputs.read_manifest(REPO)
        rels = ["docs/color-vision.md", *[f"docs/renders/{k}.svg" for k in docsgen.VARIANTS],
                *[f"docs/swatches/{name}.svg" for name in P.colors], *[f"docs/badges/{b}.svg" for b in docsgen.BADGES]]
        for rel in rels:
            self.assertEqual(manifest.get(rel), "docs", rel)
        self.assertEqual(buildcmd.build(REPO), [])

SVG = "{http://www.w3.org/2000/svg}"
GITHUB_PAGES = {"light": "#FFFFFF", "dark": "#0D1117"}  # the README's two possible page backgrounds

class DocAssetsTest(unittest.TestCase):
    def setUp(self):
        self.ports = registry.load_ports(REPO / "ports.toml")
        self.docs = docsgen.plan(REPO, P, self.ports)

    def svg(self, rel):
        owner, data = self.docs[rel]
        self.assertEqual(owner, "docs")
        return ET.fromstring(data.decode("utf-8"))

    def test_one_swatch_per_color_filled_with_its_hex(self):
        swatches = sorted(rel for rel in self.docs if rel.startswith("docs/swatches/"))
        self.assertEqual(swatches, sorted(f"docs/swatches/{name}.svg" for name in P.colors))
        for name, hx in P.colors.items():
            rect = self.svg(f"docs/swatches/{name}.svg").find(f"{SVG}rect")
            self.assertEqual(rect.get("fill"), hx, name)
            self.assertEqual(rect.get("stroke"), P.resolve("ui.text_dim"), name)

    def test_swatch_outline_stays_visible_on_both_github_themes(self):
        """Non-text contrast (WCAG 1.4.11): the outline keeps the darkest swatches visible on either page."""
        for theme, page in GITHUB_PAGES.items():
            self.assertGreaterEqual(color.contrast(P.resolve("ui.text_dim"), page), 3.0, theme)

    def test_badges_state_values_from_the_palette_and_registry(self):
        live = [p for p in self.ports if not p.archived_reason]
        ratio = f"{color.contrast(P.colors['text'], P.colors['bg']):.1f}:1"
        expected = {"license": ("license", P.meta["license"]), "release": ("release", f"v{P.meta['release']}"),
                    "ports": ("ports", str(len(live))), "contrast": ("text contrast", ratio)}
        self.assertEqual(set(docsgen.BADGES), set(expected))
        for badge, (label, value) in expected.items():
            texts = [t.text for t in self.svg(f"docs/badges/{badge}.svg").iter(f"{SVG}text")]
            self.assertEqual(texts, [label, value], badge)

    def test_badges_are_neutral_and_readable(self):
        for badge in docsgen.BADGES:
            root = self.svg(f"docs/badges/{badge}.svg")
            fills = [r.get("fill") for r in root.iter(f"{SVG}rect")]
            text_fill = {t.get("fill") for t in root.iter(f"{SVG}text")}
            self.assertEqual(text_fill, {P.colors["text"]}, badge)
            for fill in set(fills):
                self.assertIn(fill, (P.colors["surface"], P.colors["overlay"]), badge)
                self.assertGreaterEqual(color.contrast(P.colors["text"], fill), 4.5, badge)

    def test_doc_assets_are_deterministic_and_self_contained(self):
        again = docsgen.plan(REPO, P, self.ports)
        for rel, (_, data) in self.docs.items():
            self.assertEqual(again[rel][1], data, rel)
            if rel.endswith(".svg"):
                text = data.decode("utf-8")
                for banned in ("href", "<style", "<script", "foreignObject", "@import", "url("):
                    self.assertNotIn(banned, text, rel)

if __name__ == "__main__":
    unittest.main()
