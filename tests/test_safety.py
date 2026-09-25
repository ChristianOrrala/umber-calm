"""Write and read safety across the build, digest, mark and package seams (spec §3, §7.3)."""
import os, subprocess, unittest
from pathlib import Path
from tests.helpers import load_real_palette, tempdir
from tests.test_buildcmd import PORTS, fixture, mark
from tests.test_outputs import port, tpl
from umber import buildcmd, outputs, package, registry, safepath

P = load_real_palette()
NO_SYMLINKS = os.name == "nt"


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.email=1+x@users.noreply.github.com", "-c", "user.name=x",
                    "-c", "commit.gpgsign=false", *args], cwd=root, check=True, capture_output=True)


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and not p.is_symlink()}


@unittest.skipIf(NO_SYMLINKS, "symlinks need privileges on Windows")
class SymlinkContainmentTest(unittest.TestCase):
    """B2: no source is read and no destination is written through a symlink or outside the repository."""

    def setUp(self):
        self._outside = tempdir()
        self.outside = Path(self._outside.__enter__())
        self.private = self.outside / "private.txt"
        self.private.write_text("private bytes\n", encoding="utf-8")

    def tearDown(self):
        self._outside.__exit__(None, None, None)

    def assert_refused(self, fn, *args, **kw):
        with self.assertRaisesRegex(safepath.UnsafePathError, "symlink|outside the repository"):
            fn(*args, **kw)
        self.assertEqual(self.private.read_text(encoding="utf-8"), "private bytes\n")

    def test_symlinked_template_is_refused_before_any_write(self):
        with tempdir() as d:
            root = fixture(d)
            (root / "templates/demo/leak.txt").symlink_to(self.private)
            before = snapshot(root)
            self.assert_refused(buildcmd.build, root)
            self.assertEqual(snapshot(root), before)

    def test_symlinked_template_directory_is_refused(self):
        with tempdir() as d:
            root = fixture(d)
            (root / "templates/demo/sub").symlink_to(self.outside, target_is_directory=True)
            self.assert_refused(buildcmd.build, root)

    def test_symlinked_digest_input_is_refused(self):
        with tempdir() as d:
            root = fixture(d, PORTS + 'inputs = ["lua/demo/*.lua"]\n')
            (root / "lua/demo").mkdir(parents=True)
            (root / "lua/demo/groups.lua").symlink_to(self.private)
            self.assert_refused(buildcmd.build, root)

    def test_symlink_in_the_port_directory_is_refused_by_digest_and_package(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / "ports/demo/extra.txt").symlink_to(self.private)
            self.assert_refused(buildcmd.port_digest, root, "demo")
            self.assert_refused(package.package, root, root / "dist")
            self.assertFalse((root / "dist").exists())

    def test_symlinked_license_is_not_packaged(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            (root / "LICENSE").symlink_to(self.private)
            self.assert_refused(package.package, root, root / "dist")

    def test_symlinked_manifest_is_neither_read_nor_written(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            (root / outputs.MANIFEST).unlink()
            (root / outputs.MANIFEST).symlink_to(self.private)
            self.assert_refused(buildcmd.build, root)

    def test_symlinked_readme_is_neither_read_nor_written(self):
        with tempdir() as d:
            root = fixture(d)
            (root / "README.md").unlink()
            (root / "README.md").symlink_to(self.private)
            self.assert_refused(buildcmd.build, root)
            self.assertFalse((root / "ports/demo/demo.conf").exists())

    def test_symlinked_verifications_file_is_refused(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            (root / "verifications.json").symlink_to(self.private)
            self.assert_refused(mark, root, digest=registry.digest(root, ["ports/demo/demo.conf"]))
            (root / "templates/demo/demo.conf.tmpl").write_text("bg={{ surface }}\n", encoding="utf-8")
            self.assert_refused(buildcmd.build, root)
            self.assertEqual((root / "ports/demo/demo.conf").read_text(encoding="utf-8"), "bg=#201F1D\n",
                             "refused before any write")

    def test_symlinked_palette_and_registry_are_refused(self):
        for rel in ("palette/umber-calm.toml", "ports.toml"):
            with self.subTest(rel), tempdir() as d:
                root = fixture(d)
                (root / rel).rename(self.outside / "moved")
                (root / rel).symlink_to(self.outside / "moved")
                self.assert_refused(buildcmd.build, root)


@unittest.skipIf(NO_SYMLINKS, "symlinks need privileges on Windows")
class SymlinkedComponentTest(unittest.TestCase):
    """Round 2: a symlink in ANY path component is refused, even one that resolves inside the repository, and
    nothing is ever written inside .git/."""

    def test_port_directory_linked_into_git_is_refused_before_any_write(self):
        with tempdir() as d:
            root = fixture(d)
            (root / ".git/info").mkdir(parents=True)
            (root / ".git/config").write_text("[core]\n", encoding="utf-8")
            (root / "ports").mkdir()
            (root / "ports/demo").symlink_to("../.git/info", target_is_directory=True)  # the re-review repro
            (root / outputs.MANIFEST).write_text("demo\tports/demo/config\n", encoding="utf-8")
            git_before = snapshot(root / ".git")
            with self.assertRaisesRegex((outputs.BuildError, safepath.UnsafePathError), "symlink"):
                buildcmd.build(root)
            self.assertEqual(snapshot(root / ".git"), git_before, "nothing written inside .git")
            self.assertEqual(sorted(p.name for p in (root / ".git/info").iterdir()), [])

    def test_port_directory_linked_inside_the_repository_is_refused(self):
        with tempdir() as d:
            root = fixture(d)
            (root / "elsewhere").mkdir()
            (root / "ports").mkdir()
            (root / "ports/demo").symlink_to("../elsewhere", target_is_directory=True)
            with self.assertRaisesRegex((outputs.BuildError, safepath.UnsafePathError), "symlink"):
                buildcmd.build(root)
            self.assertEqual(list((root / "elsewhere").iterdir()), [])
            self.assertFalse((root / outputs.MANIFEST).exists())

    def test_symlinked_templates_directory_is_refused(self):
        for linked in ("templates", "templates/demo"):
            with self.subTest(linked), tempdir() as d:
                root = fixture(d)
                (root / linked).rename(root / "stash")
                (root / linked).symlink_to(Path("../" * linked.count("/")) / "stash", target_is_directory=True)
                with self.assertRaisesRegex(safepath.UnsafePathError, "symlink"):
                    buildcmd.build(root)
                self.assertFalse((root / "ports").exists())

    def test_sweep_symlink_in_a_port_directory_is_refused_before_any_write(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            (root / "elsewhere").mkdir()
            (root / "ports/demo/sub").symlink_to("../../elsewhere", target_is_directory=True)
            (root / "templates/demo/demo.conf.tmpl").write_text("bg={{ surface }}\n", encoding="utf-8")
            with self.assertRaisesRegex(safepath.UnsafePathError, "symlink"):
                buildcmd.build(root)
            self.assertEqual((root / "ports/demo/demo.conf").read_text(encoding="utf-8"), "bg=#201F1D\n")

    def test_nothing_resolves_into_git(self):
        with tempdir() as d:
            root = Path(d); (root / ".git").mkdir()
            for rel in (".git/config", ".GIT/config", "ports/.git/x"):
                with self.assertRaisesRegex(safepath.UnsafePathError, r"\.git"):
                    safepath.inside(root, rel)
            safepath.inside(root, "ports/demo/a.conf")


class PreflightTest(unittest.TestCase):
    """M2: the complete destination set is validated together before anything is written."""

    def test_generated_readme_collides_with_a_case_variant(self):
        with tempdir() as d:
            root = fixture(d)
            (root / "templates/demo/readme.md.tmpl").write_text("lower\n", encoding="utf-8")
            with self.assertRaisesRegex(outputs.BuildError, "only by case"):
                buildcmd.build(root)
            self.assertFalse((root / "ports/demo/demo.conf").exists())

    def test_existing_case_variant_on_disk_is_refused(self):
        with tempdir() as d:
            root = Path(d); tpl(root, "demo", "Theme.conf.tmpl", "x\n")
            (root / "ports/demo").mkdir(parents=True)
            (root / "ports/demo/theme.conf.old").write_text("x\n", encoding="utf-8")  # unrelated: fine
            outputs.write(root, outputs.plan(root, P, [port()]))
            (root / "ports/demo/Theme.conf").unlink()
            (root / "ports/demo/THEME.conf").write_text("mine\n", encoding="utf-8")
            with self.assertRaisesRegex(outputs.BuildError, "only by case"):
                outputs.preflight(root, {"ports/demo/Theme.conf": "demo"})

    def test_file_and_directory_collisions(self):
        with tempdir() as d:
            root = Path(d)
            with self.assertRaisesRegex(outputs.BuildError, "file and a directory"):
                outputs.preflight(root, {"ports/demo/a": "demo", "ports/demo/a/b": "demo"})
            (root / "ports/demo/x").mkdir(parents=True)
            with self.assertRaisesRegex(outputs.BuildError, "is a directory"):
                outputs.preflight(root, {"ports/demo/x": "demo"})
            (root / "ports/demo/f").write_text("", encoding="utf-8")
            (root / outputs.MANIFEST).write_text("demo\tports/demo/f\n", encoding="utf-8")
            with self.assertRaisesRegex(outputs.BuildError, "not a directory"):
                outputs.preflight(root, {"ports/demo/f/inner": "demo"})

    def test_control_and_windows_invalid_characters_are_rejected(self):
        for bad in ("ports/demo/a\tb", "ports/demo/a\nb", "ports/demo/a\x00b", "ports/demo/a\x1fb",
                    "ports/demo/a:stream", "ports/demo/a<b", "ports/demo/a>b", 'ports/demo/a"b',
                    "ports/demo/a|b", "ports/demo/a?b", "ports/demo/a*b"):
            with self.assertRaises(outputs.BuildError, msg=repr(bad)):
                outputs.validate_rel(bad)

    def test_manifest_is_parsed_strictly(self):
        for text, line in (("demo\tports/demo/a\nno tab here\n", 2), ("demo\tports/demo/a\n\n", 2),
                           ("\tports/demo/a\n", 1), ("demo\t\n", 1), ("demo\tports/demo/a\textra\n", 1),
                           ("Bad Owner\tports/demo/a\n", 1), ("demo\tports/demo/a\ndemo\tports/demo/a\n", 2)):
            with self.subTest(text=text), tempdir() as d:
                (Path(d) / outputs.MANIFEST).write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(outputs.BuildError, rf"\.generated-manifest:{line}:"):
                    outputs.read_manifest(Path(d))
        with tempdir() as d:
            (Path(d) / outputs.MANIFEST).write_text("demo\tports/demo/a\nreadme:demo\tports/demo/README.md\n"
                                                    "docs\tdocs/color-vision.md\n", encoding="utf-8")
            self.assertEqual(len(outputs.read_manifest(Path(d))), 3)


class PublishableInputsTest(unittest.TestCase):
    """I-1: digests and packages cover only files git would publish."""

    def test_ignored_file_changes_neither_digest_nor_package(self):
        with tempdir() as d:
            root = fixture(d)
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / ".gitignore").write_text(".DS_Store\n", encoding="utf-8")
            git(root, "init", "-q"); buildcmd.build(root)
            before = buildcmd.port_digest(root, "demo")
            first = {p.name: p.read_bytes() for p in package.package(root, Path(d) / "a")}
            (root / "ports/demo/.DS_Store").write_bytes(b"finder state")
            self.assertEqual(buildcmd.port_digest(root, "demo"), before)
            second = {p.name: p.read_bytes() for p in package.package(root, Path(d) / "b")}
            self.assertEqual(first, second)
            (root / "ports/demo/notes.txt").write_text("untracked but not ignored\n", encoding="utf-8")
            self.assertIn("ports/demo/notes.txt", buildcmd.port_digest(root, "demo")[1])

    def test_outside_git_the_sweep_skips_os_and_cache_files(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            before = buildcmd.port_digest(root, "demo")
            (root / "ports/demo/.DS_Store").write_bytes(b"finder state")
            (root / "ports/demo/__pycache__").mkdir()
            (root / "ports/demo/__pycache__/x.pyc").write_bytes(b"cache")
            self.assertEqual(buildcmd.port_digest(root, "demo"), before)


if __name__ == "__main__":
    unittest.main()
