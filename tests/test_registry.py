import dataclasses, json, unittest
from pathlib import Path
from tests.helpers import tempdir
from umber import registry

PORT = '''
[[port]]
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
D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64

def record(**kw):
    base = {"status": "verified", "date": "2026-10-02", "app_version": "1.0", "os": "macOS", "os_version": "15.1",
            "digest": D1, "note": "", "evidence": ""}
    return {**base, **kw}

def write(d, text):
    p = Path(d) / "ports.toml"; p.write_text(text, encoding="utf-8"); return p

class RegistryTest(unittest.TestCase):
    def test_loads_valid_port_with_defaults(self):
        with tempdir() as d:
            [port] = registry.load_ports(write(d, PORT))
            self.assertEqual(port.id, "demo")
            self.assertEqual(port.checklist, ("background",))
            self.assertEqual((port.risk, port.min_version, port.inputs, port.syntax_check, port.archived_reason),
                             ("", "", (), None, ""))

    def test_optional_fields(self):
        extra = ('min_version = "0.9"\ninputs = ["lua/demo/*.lua"]\n'
                 'syntax_check = { file = "demo.json", format = "vscode" }\n'
                 'archived = { reason = "app discontinued", since = "0.3.0" }\n')
        with tempdir() as d:
            [port] = registry.load_ports(write(d, PORT + extra))
            self.assertEqual(port.inputs, ("lua/demo/*.lua",))
            self.assertEqual(port.syntax_check, {"file": "demo.json", "format": "vscode"})
            self.assertEqual((port.archived_reason, port.archived_since), ("app discontinued", "0.3.0"))

    def test_rejects_bad_optional_fields(self):
        bad = ['syntax_check = { file = "x", format = "word" }\n',
               'syntax_check = { file = "../x", format = "vim" }\n',
               'syntax_check = { file = "x", format = "vim" }\nsyntax_exempt = "data"\n',
               'inputs = ["/abs/*.lua"]\n', 'inputs = ["..\\\\x"]\n',
               'archived = { reason = "", since = "0.3.0" }\n', 'archived = { reason = "r", since = "soon" }\n',
               'surprise = 1\n']
        for extra in bad:
            with tempdir() as d:
                with self.assertRaises(registry.RegistryError, msg=extra):
                    registry.load_ports(write(d, PORT + extra))

    def test_candidate_reason_is_required_exactly_for_candidates(self):
        candidate = PORT.replace("format_confirmed = true", "format_confirmed = false")
        with tempdir() as d:
            with self.assertRaisesRegex(registry.RegistryError, "candidate_reason"):
                registry.load_ports(write(d, candidate))
            with self.assertRaisesRegex(registry.RegistryError, "candidate_reason"):
                registry.load_ports(write(d, candidate + 'candidate_reason = "  "\n'))
            with self.assertRaisesRegex(registry.RegistryError, "candidate_reason"):
                registry.load_ports(write(d, PORT + 'candidate_reason = "unconfirmed"\n'))
            [port] = registry.load_ports(write(d, candidate + 'candidate_reason = "the value syntax is unconfirmed"\n'))
            self.assertEqual(port.candidate_reason, "the value syntax is unconfirmed")

    def test_rejects_missing_field(self):
        with tempdir() as d:
            with self.assertRaisesRegex(registry.RegistryError, "demo.*uninstall"):
                registry.load_ports(write(d, PORT.replace('uninstall = "Delete it."\n', "")))

    def test_rejects_bad_category_and_duplicates(self):
        with tempdir() as d:
            with self.assertRaisesRegex(registry.RegistryError, "category"):
                registry.load_ports(write(d, PORT.replace('"terminal"', '"toaster"')))
            with self.assertRaisesRegex(registry.RegistryError, "duplicate"):
                registry.load_ports(write(d, PORT + PORT))

    def test_verifications_roundtrip_and_missing_file(self):
        with tempdir() as d:
            path = Path(d) / "verifications.json"
            self.assertEqual(registry.load_verifications(path), {})
            data = {"demo": [record(evidence="https://github.com/ChristianOrrala/umber-calm/issues/12")]}
            registry.save_verifications(path, data)
            self.assertEqual(registry.load_verifications(path), data)
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))

    def test_record_schema_is_strict(self):
        bad = [record(os="macOS 15 on my-laptop"), record(os_version="15.1-beta"), record(digest="sha256:abc"),
               record(note="line one\nline two"), record(note="x" * 201), record(evidence="https://example.org/x"),
               record(date="02/10/2026"), record(date="20261002"), record(date="2026-02-30"),
               record(date="2026-10-02\n"), record(status="great"), record(app_version="1.0 /" + "home/x"),
               record(app_version="1.0 beta"), record(app_version="v1.0"), record(app_version="1..0"),
               record(app_version="1.0\n"), record(app_version="1" * 41), record(os_version="١٥"),
               {**record(), "host": "x"}]
        for rec in bad:
            with self.assertRaises(registry.RegistryError, msg=repr(rec)):
                registry.validate_record("demo", rec)
        registry.validate_record("demo", record(app_version="0.39.1", date="2028-02-29"))
        with tempdir() as d:
            path = Path(d) / "verifications.json"
            path.write_text(json.dumps({"demo": [record(os="Plan 9")]}), encoding="utf-8")
            with self.assertRaisesRegex(registry.RegistryError, "os must be"):
                registry.load_verifications(path)

    def test_evidence_scoped_to_umber_calm_repo(self):
        # Reject URLs from other GitHub repositories
        bad_repos = [
            record(evidence="https://github.com/someone/else/issues/3"),
            record(evidence="https://github.com/ChristianOrrala/other-repo/issues/5"),
            record(evidence="https://github.com/example/other/pull/42"),
        ]
        for rec in bad_repos:
            with self.assertRaises(registry.RegistryError, msg=repr(rec)):
                registry.validate_record("demo", rec)

        # Accept URLs from umber-calm repo (issues, pull, discussions)
        good_urls = [
            "https://github.com/ChristianOrrala/umber-calm/issues/1",
            "https://github.com/ChristianOrrala/umber-calm/issues/999",
            "https://github.com/ChristianOrrala/umber-calm/pull/42",
            "https://github.com/ChristianOrrala/umber-calm/discussions/7",
        ]
        for url in good_urls:
            registry.validate_record("demo", record(evidence=url))

        # Empty evidence is still allowed
        registry.validate_record("demo", record(evidence=""))

    def test_digest_depends_on_paths_and_bytes(self):
        with tempdir() as d:
            root = Path(d); (root / "a").write_text("x", encoding="utf-8")
            first = registry.digest(root, ["a"])
            self.assertRegex(first, r"^sha256:[0-9a-f]{64}$")
            (root / "a").write_text("y", encoding="utf-8")
            self.assertNotEqual(first, registry.digest(root, ["a"]))

    def test_digest_paths_cover_inputs_and_port_dir_but_not_readme(self):
        with tempdir() as d:
            root = Path(d)
            for rel in ("ports/demo/a.conf", "ports/demo/extra.txt", "ports/demo/README.md", "lua/demo/x.lua"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text(rel, encoding="utf-8")
            [port] = registry.load_ports(write(d, PORT + 'inputs = ["lua/demo/*.lua"]\n'))
            self.assertEqual(registry.digest_paths(root, port, ["ports/demo/a.conf"]),
                             ["lua/demo/x.lua", "ports/demo/a.conf", "ports/demo/extra.txt"])
            nvim = dataclasses.replace(port, output_root=".", inputs=("lua/demo/**/*.lua",))
            self.assertEqual(registry.digest_paths(root, nvim, ["colors/demo.vim"]), ["colors/demo.vim", "lua/demo/x.lua"])
            missing = dataclasses.replace(port, inputs=("doc/*.txt",))
            with self.assertRaisesRegex(registry.RegistryError, "matches no file"):
                registry.digest_paths(root, missing, [])

    def test_tiers(self):
        with tempdir() as d:
            [port] = registry.load_ports(write(d, PORT))
        unconfirmed = dataclasses.replace(port, format_confirmed=False)
        ok = record()
        self.assertEqual(registry.tier(port, [], D1).tier, "experimental")
        self.assertEqual(registry.tier(unconfirmed, [], D1).tier, "candidate")
        self.assertEqual(registry.tier(port, [ok], D1).tier, "supported")
        stale = registry.tier(port, [ok], D2)
        self.assertEqual((stale.tier, stale.stale), ("experimental", True))
        self.assertEqual(registry.tier(port, [ok, record(status="needs-fix")], D1).tier, "needs-fix")

if __name__ == "__main__":
    unittest.main()
