import unittest
from tests.helpers import tempdir
from tests.test_buildcmd import PORTS, fixture, mark
from umber import buildcmd, outputs, portreadme, registry

P = registry.Port(id="kitty", name="Kitty", category="terminal", phase=1, output_root="ports/kitty",
                  docs="https://example.invalid/docs", format_confirmed=True, target_version="0.39",
                  install="Copy it.", uninstall="Remove it.", checklist=("background", "cursor"),
                  risk="client mod", min_version="0.35")
DIGEST = "sha256:" + "ab" * 32
RECORDS = (
    {"status": "needs-fix", "date": "2026-10-01", "app_version": "0.38", "os": "Linux", "os_version": "",
     "digest": "sha256:" + "cd" * 32, "note": "tab bar unreadable", "evidence": ""},
    {"status": "verified", "date": "2026-10-02", "app_version": "0.39", "os": "macOS", "os_version": "15.1",
     "digest": DIGEST, "note": "", "evidence": "https://github.com/ChristianOrrala/umber-calm/issues/3"},
)
INFO = registry.TierInfo("supported", RECORDS[-1], False, digest=DIGEST,
                         inputs=("ports/kitty/umber-calm.conf",), records=RECORDS)


def other_port(pid: str) -> str:
    """A second [[port]] entry shaped like the fixture's demo port."""
    return "\n" + PORTS.replace('"demo"', f'"{pid}"').replace('"Demo"', f'"{pid.title()}"').replace("ports/demo", f"ports/{pid}")

class PortReadmeTest(unittest.TestCase):
    def test_render(self):
        text = portreadme.render(P, INFO)
        for needle in ("# Kitty — Umber Calm", "⚠️ **Warning:** client mod", "Tier: ✅ supported",
                       "Target version: 0.39 · Minimum version: 0.35", "## Install\n\nCopy it.",
                       "- [ ] background", f"Current digest: `{DIGEST}`", "python3 tools/build.py digest kitty",
                       "- `ports/kitty/umber-calm.conf`",
                       "| 2026-10-01 | ⚠️ needs-fix | 0.38 | Linux |  | tab bar unreadable |",
                       "[#3](https://github.com/ChristianOrrala/umber-calm/issues/3)"):
            self.assertIn(needle, text)
        self.assertLess(text.index("| 2026-10-02"), text.index("| 2026-10-01"), "newest record first")

    def test_target_version_candidate_reason_and_escaped_history(self):
        port = registry.Port(**{**P.__dict__, "format_confirmed": False, "candidate_reason": "keys unconfirmed"})
        records = ({**RECORDS[0], "note": "a | b"},)
        text = portreadme.render(port, registry.TierInfo("needs-fix", records[0], False, digest=DIGEST, records=records))
        self.assertIn("Target version: 0.39", text)
        self.assertNotIn("Tested version", text)
        self.assertIn("🟡 **Candidate:** keys unconfirmed", text)
        self.assertIn("| a \\| b |", text)
        self.assertIn("Verified on: —", text)
        self.assertIn("Verified on: 0.39 · macOS 15.1 (2026-10-02)", portreadme.render(P, INFO))

    def test_every_port_readme_has_one_footer(self):
        from tests.helpers import REPO
        for readme in sorted((REPO / "ports").glob("*/README.md")):
            self.assertEqual(readme.read_text(encoding="utf-8").lower().count("do not edit"), 1, readme.parent.name)

    def test_archived_notice(self):
        port = registry.Port(**{**P.__dict__, "archived_reason": "Upstream removed theme support.",
                                "archived_since": "0.3.0"})
        text = portreadme.render(port, registry.TierInfo("experimental", None, False, digest=DIGEST))
        self.assertIn("📦 **Archived since 0.3.0:** Upstream removed theme support.", text)
        self.assertIn("No verification recorded yet.", text)

    def test_template_readme_is_an_intro_with_the_verification_section(self):
        planned = {"ports/kitty/README.md": ("kitty", b"# Custom\n\nAbout.\n"), "ports/kitty/a.conf": ("kitty", b"x")}
        intros = portreadme.split_intros(planned, [P])
        self.assertEqual(intros, {"kitty": "# Custom\n\nAbout.\n"})
        self.assertEqual(list(planned), ["ports/kitty/a.conf"], "a template README is never a port output")
        [(rel, (owner, data))] = portreadme.plan_docs([P], {"kitty": INFO}, intros).items()
        text = data.decode("utf-8")
        self.assertEqual((rel, owner), ("ports/kitty/README.md", "readme:kitty"))
        self.assertTrue(text.startswith("# Custom\n\nAbout.\n\n> ⚠️ **Warning:** client mod"), text)
        for needle in ("Tier: ✅ supported", f"Current digest: `{DIGEST}`", "- `ports/kitty/umber-calm.conf`", "| 2026-10-01 | ⚠️ needs-fix |"):
            self.assertIn(needle, text)
        self.assertIn("## Install\n\nCopy it.", text)
        self.assertNotIn("# Kitty — Umber Calm", text, "the intro replaces the generated title")

    def test_build_writes_template_readme_with_verification_section(self):
        with tempdir() as d:
            root = fixture(d)
            (root / "templates/demo/README.md.tmpl").write_text("# Demo for {{ meta.name }}\n", encoding="utf-8")
            buildcmd.build(root)
            text = (root / "ports/demo/README.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("# Demo for Umber Calm\n\nTier: 🧪 experimental"), text)
            self.assertIn(f"Current digest: `{buildcmd.port_digest(root, 'demo')[0]}`", text)
            self.assertIn("readme:demo\tports/demo/README.md", (root / ".generated-manifest").read_text(encoding="utf-8"))
            self.assertEqual((buildcmd.stale(root), buildcmd.build(root)), ([], []))

    def test_build_and_mark_refresh_the_port_readme(self):
        with tempdir() as d:
            root = fixture(d)
            buildcmd.build(root)
            digest = buildcmd.port_digest(root, "demo")[0]
            self.assertIn(f"Current digest: `{digest}`", (root / "ports/demo/README.md").read_text(encoding="utf-8"))
            mark(root)
            text = (root / "ports/demo/README.md").read_text(encoding="utf-8")
            self.assertIn("| 2026-10-02 | ✅ verified | 1.0 | macOS | 15.1 |", text)
            self.assertEqual(buildcmd.port_digest(root, "demo")[0], digest, "a README is never part of a digest")
            self.assertEqual(buildcmd.build(root), [])

    def test_handwritten_port_readme_stops_the_build_before_any_write(self):
        with tempdir() as d:
            root = fixture(d)
            (root / "ports/demo").mkdir(parents=True)
            (root / "ports/demo/README.md").write_text("handwritten\n", encoding="utf-8")
            main_readme = (root / "README.md").read_bytes()
            with self.assertRaisesRegex(outputs.BuildError, "unowned"):
                buildcmd.build(root)
            self.assertFalse((root / "ports/demo/demo.conf").exists(), "preflight covers the README phase too")
            self.assertFalse((root / outputs.MANIFEST).exists())
            self.assertEqual((root / "README.md").read_bytes(), main_readme)
            self.assertEqual((root / "ports/demo/README.md").read_text(encoding="utf-8"), "handwritten\n")

    def test_mark_refreshes_only_documentation(self):
        with tempdir() as d:
            root = fixture(d, PORTS + 'inputs = ["ports/lib/lib.conf"]\n' + other_port("lib") + other_port("other"))
            for pid in ("lib", "other"):
                (root / f"templates/{pid}").mkdir()
                (root / f"templates/{pid}/{pid}.conf.tmpl").write_text("fg={{ blue }}\n", encoding="utf-8")
            buildcmd.build(root)
            for pid in ("lib", "other"):  # both go stale: `lib` is a dependency of demo, `other` is unrelated
                (root / f"templates/{pid}/{pid}.conf.tmpl").write_text("fg={{ green }}\n", encoding="utf-8")
            untouched = ["ports/lib/lib.conf", "ports/lib/README.md", "ports/other/other.conf",
                         "ports/other/README.md", outputs.MANIFEST]
            before = {rel: (root / rel).read_bytes() for rel in untouched}
            mark(root, digest=buildcmd.states(root)["demo"].digest)
            self.assertEqual({rel: (root / rel).read_bytes() for rel in untouched}, before)
            self.assertEqual(buildcmd.stale(root), ["ports/lib/lib.conf", "ports/other/other.conf"])
            self.assertIn("| 2026-10-02 | ✅ verified |", (root / "ports/demo/README.md").read_text(encoding="utf-8"))
            self.assertIn("✅ supported", (root / "README.md").read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
