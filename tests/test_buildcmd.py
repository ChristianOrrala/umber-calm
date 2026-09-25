import json, shutil, subprocess, sys, unittest
from pathlib import Path
from tests.helpers import REPO, PALETTE_PATH, tempdir
from umber import buildcmd, registry

PORTS = '''[[port]]
id = "demo"
name = "Demo"
category = "terminal"
phase = 1
output_root = "ports/demo"
docs = "internal"
format_confirmed = true
target_version = "1.0"
install = "Copy it."
uninstall = "Delete it."
checklist = ["background"]
'''
README = "# x\n<!-- palette:begin -->\n<!-- palette:end -->\n<!-- ports:begin -->\n<!-- ports:end -->\n" \
         "<!-- verification:begin -->\n<!-- verification:end -->\n"

def fixture(d, ports=PORTS) -> Path:
    root = Path(d)
    (root / "palette").mkdir(); shutil.copy(PALETTE_PATH, root / "palette/umber-calm.toml")
    (root / "ports.toml").write_text(ports, encoding="utf-8")
    (root / "README.md").write_text(README, encoding="utf-8")
    t = root / "templates/demo"; t.mkdir(parents=True)
    (t / "demo.conf.tmpl").write_text("bg={{ bg }}\n", encoding="utf-8")
    return root

def mark(root, pid="demo", status="verified", **kw):
    """Call buildcmd.mark with valid defaults; the digest defaults to the port's current one."""
    if "digest" not in kw:
        kw["digest"] = buildcmd.port_digest(root, pid)[0] if pid == "demo" else "sha256:" + "0" * 64
    args = dict(app_version="1.0", os_name="macOS", os_version="15.1", note="", evidence="", today="2026-10-02")
    return buildcmd.mark(root, pid, status, **{**args, **kw})

class BuildCmdTest(unittest.TestCase):
    def test_build_generates_and_is_idempotent(self):
        with tempdir() as d:
            root = fixture(d)
            changed = buildcmd.build(root)
            self.assertIn("ports/demo/demo.conf", changed)
            self.assertIn("README.md", changed)
            self.assertIn("🧪 experimental", (root / "README.md").read_text(encoding="utf-8"))
            self.assertEqual(buildcmd.build(root), [])

    def test_mark_then_template_change_expires_verification(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            mark(root)
            self.assertIn("✅ supported", (root / "README.md").read_text(encoding="utf-8"))
            (root / "templates/demo/demo.conf.tmpl").write_text("bg={{ surface }}\n", encoding="utf-8")
            buildcmd.build(root)
            text = (root / "README.md").read_text(encoding="utf-8")
            self.assertIn("🧪 experimental", text)
            self.assertIn("2026-10-02 (earlier revision)", text)

    def test_mark_never_builds_and_refuses_stale_outputs(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            tested = buildcmd.port_digest(root, "demo")[0]
            (root / "templates/demo/demo.conf.tmpl").write_text("bg={{ surface }}\n", encoding="utf-8")
            with self.assertRaisesRegex(buildcmd.CommandError, "stale"):
                mark(root, digest=tested)
            self.assertEqual((root / "ports/demo/demo.conf").read_text(encoding="utf-8"), "bg=#201F1D\n")
            self.assertFalse((root / "verifications.json").exists())

    def test_mark_refuses_a_digest_that_does_not_match(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            with self.assertRaisesRegex(buildcmd.CommandError, "does not match"):
                mark(root, digest="sha256:" + "0" * 64)
            (root / "ports/demo/notes.txt").write_text("extra file in the port directory\n", encoding="utf-8")
            with self.assertRaisesRegex(buildcmd.CommandError, "does not match"):
                mark(root, digest=registry.digest(root, ["ports/demo/demo.conf"]))
            self.assertFalse((root / "verifications.json").exists())

    def test_inputs_are_part_of_the_digest(self):
        ports = PORTS + 'inputs = ["lua/demo/*.lua"]\n'
        with tempdir() as d:
            root = fixture(d, ports)
            (root / "lua/demo").mkdir(parents=True); (root / "lua/demo/groups.lua").write_text("-- v1\n", encoding="utf-8")
            buildcmd.build(root); mark(root)
            value, files = buildcmd.port_digest(root, "demo")
            self.assertIn("lua/demo/groups.lua", files)
            (root / "lua/demo/groups.lua").write_text("-- v2\n", encoding="utf-8")
            buildcmd.build(root)
            self.assertIn("(earlier revision)", (root / "README.md").read_text(encoding="utf-8"))

    def test_mark_validates_free_text(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            for kw, needle in ((dict(note="tested on /" + "Users/alice/box"), "personal data"),
                               (dict(evidence="https://github.com/someone/else/issues/1"), "evidence"),
                               (dict(os_version="15 (my-laptop)"), "os_version"),
                               (dict(app_version="0.39 nightly"), "app_version"),
                               (dict(today="20261002"), "date"),
                               (dict(os_name="Plan 9"), "os must be")):
                with self.assertRaisesRegex(buildcmd.CommandError, needle):
                    mark(root, **kw)
            self.assertFalse((root / "verifications.json").exists())
            mark(root, evidence="https://github.com/ChristianOrrala/umber-calm/issues/3", app_version="v0.39.1")
            [saved] = json.loads((root / "verifications.json").read_text(encoding="utf-8"))["demo"]
            self.assertEqual(saved["app_version"], "0.39.1", "a leading v is dropped")

    def test_digest_refuses_stale_outputs(self):
        with tempdir() as d:
            root = fixture(d)
            with self.assertRaisesRegex(buildcmd.CommandError, "stale"):
                buildcmd.port_digest(root, "demo")
            buildcmd.build(root)
            value, files = buildcmd.port_digest(root, "demo")
            self.assertRegex(value, r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(files, ["ports/demo/demo.conf"])

    def test_mark_unknown_port(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            with self.assertRaisesRegex(buildcmd.CommandError, "unknown port 'nope'"):
                mark(root, "nope")
            self.assertFalse((root / "verifications.json").exists())

    def test_mark_port_without_outputs(self):
        with tempdir() as d:
            root = fixture(d)
            (root / "templates/demo/demo.conf.tmpl").unlink()
            with self.assertRaisesRegex(buildcmd.CommandError, "no generated files"):
                mark(root, digest="sha256:" + "0" * 64)
            self.assertFalse((root / "verifications.json").exists())

    def test_mark_rejects_bad_status(self):
        with tempdir() as d:
            root = fixture(d)
            with self.assertRaisesRegex(buildcmd.CommandError, "status"):
                mark(root, status="great", digest="sha256:" + "0" * 64)

    def test_cli_runs_from_other_cwd(self):
        with tempdir() as d:
            result = subprocess.run([sys.executable, str(REPO / "tools/build.py"), "--help"],
                                    cwd=d, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("mark", result.stdout)
            self.assertIn("digest", result.stdout)

if __name__ == "__main__":
    unittest.main()
