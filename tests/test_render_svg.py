import json, re, unittest
import xml.etree.ElementTree as ET
from tests.helpers import REPO, load_real_palette
from umber import buildcmd, cvd, docsgen, outputs, render_svg

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

    def test_build_writes_the_generated_docs(self):
        buildcmd.build(REPO)
        manifest = outputs.read_manifest(REPO)
        for rel in ["docs/color-vision.md", *[f"docs/renders/{k}.svg" for k in docsgen.VARIANTS]]:
            self.assertEqual(manifest.get(rel), "docs", rel)
        self.assertEqual(buildcmd.build(REPO), [])

if __name__ == "__main__":
    unittest.main()
