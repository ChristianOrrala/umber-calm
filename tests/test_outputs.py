import os, unittest
from pathlib import Path
from tests.helpers import load_real_palette, tempdir
from umber import outputs, readme, registry

P = load_real_palette()

def port(pid="demo", root=None, **kw):
    base = dict(id=pid, name=pid.title(), category="terminal", phase=1, output_root=root or f"ports/{pid}",
                docs="internal", format_confirmed=True, target_version="1", install="i", uninstall="u",
                checklist=("background",))
    return registry.Port(**{**base, **kw})

def tpl(root: Path, pid: str, rel: str, text: str):
    p = root / "templates" / pid / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")

class OutputsTest(unittest.TestCase):
    def test_plan_render_and_copy(self):
        with tempdir() as d:
            root = Path(d); tpl(root, "demo", "demo.conf.tmpl", "bg={{ bg }}\n"); tpl(root, "demo", "icon.txt", "raw {{ bg }}\n")
            planned = outputs.plan(root, P, [port()])
            self.assertEqual(planned["ports/demo/demo.conf"], ("demo", b"bg=#201F1D\n"))
            self.assertEqual(planned["ports/demo/icon.txt"], ("demo", b"raw {{ bg }}\n"))

    def test_template_dirs_must_match_registry(self):
        with tempdir() as d:
            root = Path(d); tpl(root, "other", "x.tmpl", "")
            with self.assertRaisesRegex(outputs.BuildError, "demo"):
                outputs.plan(root, P, [port()])

    def test_outside_roots_and_collisions(self):
        with tempdir() as d:
            root = Path(d); tpl(root, "demo", "x.tmpl", "")
            with self.assertRaisesRegex(outputs.BuildError, "unsafe|outside the allowed roots"):
                outputs.plan(root, P, [port(root="../evil")])
        with tempdir() as d:
            root = Path(d); tpl(root, "a", "x.tmpl", ""); tpl(root, "b", "x.tmpl", "")
            with self.assertRaisesRegex(outputs.BuildError, "collision"):
                outputs.plan(root, P, [port("a", root="ports/same"), port("b", root="ports/same")])
        with tempdir() as d:
            root = Path(d); tpl(root, "a", "Theme.tmpl", ""); tpl(root, "b", "theme.tmpl", "")
            with self.assertRaisesRegex(outputs.BuildError, "only by case"):
                outputs.plan(root, P, [port("a", root="ports/same"), port("b", root="ports/same")])

    def test_validate_rel_rejects_unportable_paths(self):
        for bad in ("ports/demo/..\\..\\LICENSE", "C:/x/ports/a", "//server/share/a", "/ports/a", "ports//a",
                    "ports/./a", "ports/demo/../../x", "ports/demo/CON", "ports/demo/nul.txt", "ports/demo/a.",
                    "ports/demo/a ", "README.md", "lua/umber-calm/groups/x.lua"):
            with self.assertRaises(outputs.BuildError, msg=bad):
                outputs.validate_rel(bad)
        for good in ("ports/demo/a.conf", "colors/umber-calm.vim", "lua/umber-calm/palette.lua",
                     "docs/color-vision.md", "docs/renders/normal.svg"):
            outputs.validate_rel(good)

    def test_write_is_idempotent_and_cleans_orphans(self):
        with tempdir() as d:
            root = Path(d); tpl(root, "demo", "a.tmpl", "1\n"); tpl(root, "demo", "b.tmpl", "2\n")
            changed = outputs.write(root, outputs.plan(root, P, [port()]))
            self.assertEqual(sorted(changed), ["ports/demo/a", "ports/demo/b"])
            self.assertEqual(outputs.write(root, outputs.plan(root, P, [port()])), [])
            (root / "templates/demo/b.tmpl").unlink()
            self.assertEqual(outputs.write(root, outputs.plan(root, P, [port()])), ["ports/demo/b"])
            self.assertFalse((root / "ports/demo/b").exists())
            self.assertEqual(outputs.read_manifest(root), {"ports/demo/a": "demo"})

    def test_stale_reports_without_writing(self):
        with tempdir() as d:
            root = Path(d); tpl(root, "demo", "a.tmpl", "1\n")
            planned = outputs.plan(root, P, [port()])
            self.assertEqual(outputs.stale(root, planned), ["ports/demo/a"])
            self.assertFalse((root / "ports/demo/a").exists())
            outputs.write(root, planned)
            self.assertEqual(outputs.stale(root, planned), [])

    def test_manifest_outside_roots_refused(self):
        with tempdir() as d:
            root = Path(d); tpl(root, "demo", "a.tmpl", "1\n")
            (root / outputs.MANIFEST).write_text("demo\t../../victim\n", encoding="utf-8")
            with self.assertRaisesRegex(outputs.BuildError, "refusing to delete"):
                outputs.write(root, outputs.plan(root, P, [port()]))
            self.assertFalse((root / "ports/demo/a").exists())

    def test_unowned_file_is_never_overwritten(self):
        with tempdir() as d:
            root = Path(d); tpl(root, "demo", "a.tmpl", "1\n"); tpl(root, "demo", "b.tmpl", "2\n")
            (root / "ports/demo").mkdir(parents=True); (root / "ports/demo/b").write_text("handwritten\n", encoding="utf-8")
            with self.assertRaisesRegex(outputs.BuildError, "unowned"):
                outputs.write(root, outputs.plan(root, P, [port()]))
            self.assertEqual((root / "ports/demo/b").read_text(encoding="utf-8"), "handwritten\n")
            self.assertFalse((root / "ports/demo/a").exists())  # preflight: nothing written

    def test_byte_identical_unowned_file_is_refused_not_adopted(self):
        with tempdir() as d:
            root = Path(d); tpl(root, "demo", "a.tmpl", "1\n")
            (root / "ports/demo").mkdir(parents=True); (root / "ports/demo/a").write_text("1\n", encoding="utf-8")
            with self.assertRaisesRegex(outputs.BuildError, "unowned"):
                outputs.write(root, outputs.plan(root, P, [port()]))
            with self.assertRaisesRegex(outputs.BuildError, "unowned"):
                outputs.preflight(root, {"ports/demo/a": "demo"})
            self.assertFalse((root / outputs.MANIFEST).exists(), "an unowned file is never adopted")

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_symlinked_directory_cannot_escape(self):
        with tempdir() as d, tempdir() as outside:
            root = Path(d); tpl(root, "demo", "a.tmpl", "1\n")
            (root / "ports").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(outputs.BuildError, "symlink|outside the repository"):
                outputs.write(root, outputs.plan(root, P, [port()]))
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_build_writes_utf8(self):
        with tempdir() as d:
            root = Path(d); tpl(root, "demo", "a.tmpl", "— {{ meta.name }}\n")
            outputs.write(root, outputs.plan(root, P, [port()]))
            self.assertEqual((root / "ports/demo/a").read_bytes(), "— Umber Calm\n".encode("utf-8"))

class ReadmeTest(unittest.TestCase):
    def test_replace_section(self):
        text = "a\n<!-- ports:begin -->\nold\n<!-- ports:end -->\nz\n"
        self.assertEqual(readme.replace_section(text, "ports", "new"),
                         "a\n<!-- ports:begin -->\nnew\n<!-- ports:end -->\nz\n")
        with self.assertRaisesRegex(readme.ReadmeError, "palette"):
            readme.replace_section(text, "palette", "x")

    def test_tables(self):
        p = port(risk="client mod", min_version="0.9")
        info = {"demo": registry.TierInfo("experimental", None, False)}
        self.assertIn("| `bg` | `#201F1D` | — |", readme.palette_table(P))
        table = readme.ports_table([p], info)
        self.assertIn("🧪 experimental", table)
        self.assertIn("⚠️ client mod", table)
        self.assertIn("1 (min 0.9)", table)
        last = {"status": "verified", "date": "2026-10-02", "app_version": "1", "os": "macOS", "os_version": "15",
                "digest": "sha256:" + "a" * 64, "note": "", "evidence": ""}
        stale = {"demo": registry.TierInfo("experimental", last, True, digest="sha256:" + "b" * 64)}
        text = readme.verification_table([p], stale)
        self.assertIn("2026-10-02 (earlier revision)", text)
        self.assertIn("macOS 15", text)
        self.assertIn("`bbbbbbbbbbbb`", text)

    def test_ports_table_reasons_notes_versions_and_root_links(self):
        cand = port("cand", format_confirmed=False, candidate_reason="value syntax | unconfirmed")
        fix = port("fix", risk="client mod")
        root = port("neovim", root=".")
        verified = {"status": "verified", "date": "2026-10-02", "app_version": "0.11.2", "os": "macOS", "os_version": "15",
                    "digest": "sha256:" + "a" * 64, "note": "", "evidence": ""}
        broken = {**verified, "status": "needs-fix", "note": "tab bar | unreadable"}
        info = {"cand": registry.TierInfo("candidate", None, False),
                "fix": registry.TierInfo("needs-fix", broken, False),
                "neovim": registry.TierInfo("supported", verified, False)}
        table = readme.ports_table([cand, fix, root], info)
        header = table.splitlines()[0]
        self.assertIn("Target version", header)
        self.assertIn("Verified on", header)
        self.assertNotIn("Tested version", header)
        rows = {line.split(" | ")[0][2:]: line for line in table.splitlines()[2:]}
        self.assertIn("🟡 value syntax \\| unconfirmed", rows["Cand"])
        self.assertIn("⚠️ needs-fix: tab bar \\| unreadable", rows["Fix"])
        self.assertIn("⚠️ client mod", rows["Fix"])
        self.assertIn("0.11.2 · macOS 15", rows["Neovim"])
        self.assertIn("[ports/neovim/](ports/neovim/README.md)", rows["Neovim"])
        self.assertNotIn("[./](./)", table)
        for row in table.splitlines()[2:]:
            self.assertEqual(row.replace("\\|", "").count("|"), header.count("|"), row)

    def test_table_cells_escape_pipes_and_newlines(self):
        self.assertEqual(readme.cell("a | b\nc\r\nd"), "a \\| b c d")

    def test_archived_ports_are_listed_separately(self):
        live, old = port("live"), port("old", archived_reason="app discontinued", archived_since="0.3.0")
        info = {pid: registry.TierInfo("experimental", None, False) for pid in ("live", "old")}
        table = readme.ports_table([live, old], info)
        main, _, archived = table.partition("**Archived**")
        self.assertIn("| Live |", main)
        self.assertNotIn("| Old |", main)
        self.assertIn("📦 archived — app discontinued", archived)

if __name__ == "__main__":
    unittest.main()
