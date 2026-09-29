import re, shutil, subprocess, unittest
from pathlib import Path
from tests.helpers import REPO, tempdir
from tests.test_buildcmd import fixture, mark
from umber import buildcmd, package, palette, release

def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

def commit_all(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-qm", message)

def repo(d) -> Path:
    root = fixture(d)
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    git(root, "init", "-q")
    git(root, "config", "user.email", "1+x@users.noreply.github.com")
    git(root, "config", "user.name", "x")
    git(root, "config", "core.autocrlf", "false")
    buildcmd.build(root)
    return root

def tag(root: Path) -> str:
    return "v" + palette.load(root / "palette/umber-calm.toml").meta["release"]

class ReleaseGateTest(unittest.TestCase):
    def test_passes_when_verified_packaged_and_committed(self):
        with tempdir() as d:
            root = repo(d)
            mark(root)
            package.package(root, root / "dist")
            commit_all(root, "release")
            self.assertEqual(release.gate(root, tag(root), launch=("demo",)), [])

    def test_reports_every_problem(self):
        with tempdir() as d:
            root = repo(d)
            commit_all(root, "no verification, no checksums")
            found = "\n".join(release.gate(root, "v9.9.9", launch=("demo", "ghost")))
            for needle in ("does not match meta.release", "launch port 'demo' is experimental",
                           "launch port 'ghost' is not in ports.toml", "dist/SHA256SUMS is not committed"):
                self.assertIn(needle, found)
            package.package(root, root / "dist")
            (root / "dist/SHA256SUMS").write_text("0" * 64 + "  umber-calm-demo-0.0.0.zip\n", encoding="utf-8")
            commit_all(root, "wrong checksums")
            self.assertIn("differ from dist/SHA256SUMS", "\n".join(release.gate(root, tag(root), launch=())))
            (root / "untracked.txt").write_text("x\n", encoding="utf-8")
            self.assertIn("working tree is not clean", "\n".join(release.gate(root, tag(root), launch=())))

    def released(self, d) -> Path:
        root = repo(d)
        shutil.copytree(REPO / "tests/fixtures", root / "tests/fixtures")  # generated docs need the sample fixture
        buildcmd.build(root)
        mark(root)
        package.package(root, root / "dist")
        commit_all(root, "release")
        self.assertEqual(release.gate(root, tag(root), launch=("demo",)), [])
        return root

    def assert_stale(self, root, needle):
        commit_all(root, "edited without building")
        found = "\n".join(release.gate(root, tag(root), launch=("demo",)))
        self.assertIn("generated files are stale", found)
        self.assertIn(needle, found)
        with self.assertRaisesRegex(package.PackageError, re.escape(needle)):
            package.package(root, root.parent / "out")

    def test_edited_install_text_fails_the_gate(self):
        with tempdir() as d:
            root = self.released(d)
            text = (root / "ports.toml").read_text(encoding="utf-8").replace("Copy it.", "Copy it somewhere.")
            (root / "ports.toml").write_text(text, encoding="utf-8")
            self.assert_stale(root, "ports/demo/README.md")

    def test_tampered_readme_section_fails_the_gate(self):
        with tempdir() as d:
            root = self.released(d)
            text = (root / "README.md").read_text(encoding="utf-8").replace("`#201F1D`", "`#000000`", 1)
            (root / "README.md").write_text(text, encoding="utf-8")
            self.assert_stale(root, "README.md")

    def test_tampered_generated_doc_fails_the_gate(self):
        with tempdir() as d:
            root = self.released(d)
            (root / "docs/color-vision.md").write_text("tampered\n", encoding="utf-8")
            self.assert_stale(root, "docs/color-vision.md")

    def test_manifest_drift_and_orphans_fail_the_gate(self):
        with tempdir() as d:
            root = self.released(d)
            (root / "ports/demo/old.conf").write_text("from an earlier build\n", encoding="utf-8")
            with open(root / ".generated-manifest", "a", encoding="utf-8", newline="") as f:
                f.write("demo\tports/demo/old.conf\n")
            self.assert_stale(root, "ports/demo/old.conf")
            found = "\n".join(release.gate(root, tag(root), launch=("demo",)))
            self.assertIn(".generated-manifest", found)

class ReleaseWorkflowTest(unittest.TestCase):
    def test_test_job_rebuilds_and_requires_a_clean_tree(self):
        text = (REPO / ".github/workflows/release.yml").read_text(encoding="utf-8")
        job = text[text.index("\n  test:"):text.index("\n  neovim:")]
        self.assertIn("run: python tools/build.py", job)
        self.assertIn("git status --porcelain", job)
        self.assertLess(job.index("tools/build.py"), job.index("tools/check.py"))

if __name__ == "__main__":
    unittest.main()
