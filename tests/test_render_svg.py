import json, re, unittest
import xml.etree.ElementTree as ET
from tests.helpers import REPO, load_real_palette
from umber import buildcmd, color, cvd, docsgen, outputs, registry, render_svg, sessions

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
                *[f"docs/renders/session-{n}.svg" for n in sessions.NAMES], "docs/renders/color-vision.svg",
                *[f"docs/swatches/{name}.svg" for name in P.colors], *[f"docs/badges/{b}.svg" for b in docsgen.BADGES]]
        for rel in rels:
            self.assertEqual(manifest.get(rel), "docs", rel)
        self.assertEqual(buildcmd.build(REPO), [])

SVG = "{http://www.w3.org/2000/svg}"

class SessionsTest(unittest.TestCase):
    """The README's calm sessions keep the palette's contracts: amber only where you are, red only a deletion."""
    def setUp(self):
        self.svgs = {name: ET.fromstring(sessions.render(name, P)) for name in sessions.NAMES}

    def fills(self, root):
        """Every painted color: fills and strokes, so a decorative outline cannot slip past the contracts."""
        return [(el, el.get(attr)) for el in root.iter() for attr in ("fill", "stroke") if el.get(attr)]

    def label(self, el):
        return "".join(el.itertext()) if el.tag in (f"{SVG}text", f"{SVG}tspan") else el.tag.rsplit("}", 1)[1]

    def test_every_color_is_a_palette_color(self):
        allowed = set(P.colors.values()) | set(P.ansi.values())
        for name, root in self.svgs.items():
            for el, fill in self.fills(root):
                self.assertIn(fill, allowed, f"{name}: {self.label(el)}")

    def test_amber_marks_only_the_focused_elements(self):
        focus = P.resolve("ui.focus")
        expected = {"claude": ["rect", "rect"],                    # cursor, active mode chip
                    "editor": ["rect", "rect", "rect"],            # active tab, cursor, mode segment
                    "terminal": ["rect", "1:brew*"]}               # cursor, current window
        for name, root in self.svgs.items():
            found = sorted(self.label(el) for el, fill in self.fills(root) if fill == focus)
            self.assertEqual(found, sorted(expected[name]), name)

    def test_red_only_marks_the_deletion(self):
        reds = {P.colors["red"], P.ansi["bright_red"]}
        for name in ("editor", "terminal"):
            self.assertFalse([f for _, f in self.fills(self.svgs[name]) if f in reds], name)
        red_text = [self.label(el) for el, fill in self.fills(self.svgs["claude"]) if fill in reds]
        self.assertEqual(sorted(red_text), sorted(["-1", "-1", "-1", " 5", " -"]))

    def test_every_drawn_pair_is_readable(self):
        """Measures the pairs each render actually draws (recorded while drawing), not a hand-kept list."""
        for name in sessions.NAMES:
            texts, marks = sessions.drawn_pairs(name, P)
            self.assertTrue(texts, name)
            for fg, bg in texts:
                ratio = color.contrast(P.resolve(fg), P.resolve(bg))
                self.assertGreaterEqual(ratio, sessions.minimum(fg, bg), f"{name}: {fg} on {bg} is {ratio:.2f}:1")
            for fg, bg in marks:  # non-text marks that carry meaning (WCAG 1.4.11)
                self.assertGreaterEqual(color.contrast(P.resolve(fg), P.resolve(bg)), 3.0, f"{name}: {fg} on {bg}")

    def test_pair_minimums_follow_the_documented_exception(self):
        self.assertEqual(sessions.minimum("ui.text", "ui.surface"), 4.5)
        self.assertEqual(sessions.minimum("ui.text_secondary", "ui.bg"), 4.5)
        self.assertEqual(sessions.minimum("ui.text_secondary", "ui.surface"), 4.0)

    def test_sessions_are_deterministic_and_self_contained(self):
        for name in sessions.NAMES:
            text = sessions.render(name, P)
            self.assertEqual(text, sessions.render(name, P), name)
            for banned in ("href", "<style", "<script", "foreignObject", "@import", "url(http"):
                self.assertNotIn(banned, text, name)

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

    def test_color_vision_strip_matches_the_readme_width(self):
        root = self.svg("docs/renders/color-vision.svg")
        self.assertEqual(float(root.get("width")), docsgen.STRIP_WIDTH)
        nested = root.findall(f"{SVG}svg")
        self.assertEqual(len(nested), len(docsgen.STRIP))
        right_edge = max(float(n.get("x")) + float(n.get("width")) for n in nested)
        self.assertAlmostEqual(right_edge, docsgen.STRIP_WIDTH, delta=0.2)
        labels = [t.text for t in root.findall(f"{SVG}text")]
        self.assertEqual(labels, [k.capitalize() for k in docsgen.STRIP])
        self.assertGreaterEqual(color.contrast(P.colors["text"], P.colors["bg"]), 4.5)

    def test_doc_assets_are_deterministic_and_self_contained(self):
        again = docsgen.plan(REPO, P, self.ports)
        for rel, (_, data) in self.docs.items():
            self.assertEqual(again[rel][1], data, rel)
            if rel.endswith(".svg"):
                text = data.decode("utf-8")
                for banned in ("href", "<style", "<script", "foreignObject", "@import", "url(http"):
                    self.assertNotIn(banned, text, rel)
                self.assertEqual(set(re.findall(r"url\(([^)]*)\)", text)) - {"#card"}, set(), rel)  # local refs only

if __name__ == "__main__":
    unittest.main()
