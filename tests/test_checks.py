import unittest
from pathlib import Path
from tests.helpers import REPO, load_real_palette, write_temp_palette, tempdir
from tests.test_buildcmd import PORTS, fixture
from umber import buildcmd, checks, hygiene, palette, readability

SHA = "a" * 40

def run_with(root, rel, text):
    path = root / rel; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    buildcmd.build(root)
    return checks.run(root)

class ReadabilityTest(unittest.TestCase):
    def test_real_palette_passes(self):
        self.assertEqual(readability.problems(load_real_palette()), [])

    def test_darker_comment_fails(self):
        with tempdir() as d:
            path = write_temp_palette(d, {'muted       = "#938A7B"': 'muted       = "#6A6357"'})
            found = readability.problems(palette.load(path))
            self.assertTrue(any("muted" in p for p in found), found)

    def test_dark_ansi_slot_fails(self):
        with tempdir() as d:
            path = write_temp_palette(d, {'bright_black   = "dim_text"': 'bright_black   = "inactive"'})
            found = readability.problems(palette.load(path))
            self.assertTrue(any("ansi.bright_black" in p for p in found), found)

    def test_light_diff_rows_are_measured(self):
        self.assertIn("#303127", readability.measured_blends(load_real_palette()))  # green at tint.diag

class ChecksTest(unittest.TestCase):
    def test_clean_fixture_passes(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            self.assertEqual(checks.run(root), [])

    def test_unresolved_placeholder(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            (root / "ports/demo/demo.conf").write_text("bg={{ bg }}\n", encoding="utf-8")
            self.assertTrue(any("unresolved" in p for p in checks.run(root)))

    def test_escaped_braces_pass_the_whole_check(self):
        with tempdir() as d:
            root = fixture(d)
            found = run_with(root, "templates/demo/literal.txt.tmpl", 'use {{ "{{" }} name }} here\n')
            self.assertEqual((root / "ports/demo/literal.txt").read_text(encoding="utf-8"), "use {{ name }} here\n")
            self.assertEqual(found, [])

    def test_invalid_json_and_xml_output(self):
        with tempdir() as d:
            root = fixture(d)
            (root / "templates/demo/x.json.tmpl").write_text("{ nope", encoding="utf-8")
            found = run_with(root, "templates/demo/y.xml.tmpl", "<a><b></a>")
            self.assertTrue(any("x.json" in p for p in found), found)
            self.assertTrue(any("y.xml" in p for p in found), found)

    def test_unmeasured_blend_fails_and_measured_blend_passes(self):
        with tempdir() as d:
            root = fixture(d)
            found = run_with(root, "templates/demo/state.conf.tmpl",
                             "ok={{ diag.diff_add | blend(bg, tint.diag) }}\nbad={{ green | blend(bg, 0.30) }}\n")
            self.assertEqual([p for p in found if "measured" in p],
                             ["readability: templates/demo/state.conf.tmpl:2: blend result #494C35 is not a measured state (spec §4.4)"])

    def test_syntax_ports_must_declare_a_check(self):
        with tempdir() as d:
            root = fixture(d)
            found = run_with(root, "templates/demo/syn.conf.tmpl", "keyword={{ syntax.keyword }}\n")
            self.assertTrue(any("syntax_check" in p for p in found), found)
        with tempdir() as d:
            root = fixture(d, PORTS + 'syntax_exempt = "exports role values as data"\n')
            self.assertEqual(run_with(root, "templates/demo/syn.conf.tmpl", "keyword={{ syntax.keyword }}\n"), [])
        with tempdir() as d:
            root = fixture(d, PORTS.replace('"terminal"', '"editor"'))
            buildcmd.build(root)
            self.assertTrue(any("syntax_check" in p for p in checks.run(root)))

    def test_hygiene_patterns_do_not_echo_matches(self):
        home = "/" + "Users" + "/alice/secret"
        win = "C:" + "\\" + "Users" + "\\" + "alice"
        ip = "192" + ".168.1.7"
        mail = "someone" + "@" + "example.org"
        host = "alice-box" + ".local"
        with tempdir() as d:
            root = fixture(d)
            found = "\n".join(run_with(root, "templates/demo/leak.txt.tmpl", f"{home}\n{win}\n{ip}\n{mail}\n{host}\n"))
            for needle in ("hygiene: home path in", "Windows home path in", "private IP in", "email in", "local hostname in"):
                self.assertIn(needle, found)
            self.assertIn("ports/demo/leak.txt:3", found)
            for secret in ("alice", "192.168", "example.org"):
                self.assertNotIn(secret, found)

    def test_hygiene_patterns_are_linear_time(self):
        import time
        for blob in ("a" * 1_000_000, "a-" * 500_000, "a." * 500_000, "x@" + "a." * 500_000, "a1" * 500_000):
            start = time.perf_counter()
            hygiene.scan_text(blob, "big")
            self.assertLess(time.perf_counter() - start, 2.0, blob[:4])
        for address in ("someone" + "@example.org", "a.b+c" + "@mail.example.co.uk"):
            self.assertEqual(len(hygiene.scan_text(f"mail {address} now", "x")), 1, address)
        self.assertEqual(hygiene.scan_text("1+x@users.noreply.github.com and noreply@github.com", "x"), [])

    def test_noreply_email_and_dotlocal_dir_allowed(self):
        with tempdir() as d:
            root = fixture(d)
            text = "1+someone" + "@users.noreply.github.com\ncopy it to ~/.local/share/themes\n"
            self.assertEqual(run_with(root, "templates/demo/ok.txt.tmpl", text), [])

    def test_repository_hygiene(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            (root / "plugin").mkdir()
            (root / "assets").mkdir(); (root / "assets/big.png").write_bytes(b"\0" * (5 * 1024 * 1024 + 1))
            found = "\n".join(checks.run(root))
            self.assertIn("plugin/ is reserved", found)
            self.assertIn("asset budget", found)

    def test_readme_links_must_resolve(self):
        with tempdir() as d:
            root = fixture(d)
            readme = (root / "README.md").read_text(encoding="utf-8")
            (root / "README.md").write_text("[Install](#install) · [Design](#design)\n## Install\n" + readme, encoding="utf-8")
            buildcmd.build(root)
            self.assertEqual([p for p in checks.run(root) if "readme" in p], ["readme: link #design has no matching heading"])

    def test_workflows_must_pin_actions(self):
        with tempdir() as d:
            root = fixture(d)
            found = run_with(root, ".github/workflows/ci.yml",
                             "steps:\n  - uses: actions/checkout@v4\n"
                             f"  - uses: actions/setup-python@{SHA} # v5.3.0\n")
            self.assertTrue(any("ci.yml:2: pin actions" in p for p in found), found)
            self.assertTrue(any("persist-credentials" in p for p in found), found)
            self.assertFalse(any("ci.yml:3" in p for p in found), found)

    def test_wording_rules(self):
        with tempdir() as d:
            root = fixture(d)
            found = run_with(root, "docs/design.md",
                             "I made this palette for my own eyes.\nIt reduces eye strain.\nDiagnostics use red.\n"
                             "It prevents headaches.\nGentle on your eyes.\nIt cures fatigue.\n")
            self.assertEqual(sorted(p for p in found if p.startswith("wording")),
                             [f"wording: health or outcome claim in docs/design.md:{n} (spec §11.2)" for n in (2, 4, 5, 6)])

    def test_asset_pngs_carry_no_metadata(self):
        import struct, zlib
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        head = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        body = chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00")) + chunk(b"IEND", b"")
        cases = {"clean.png": head + body, "text.png": head + chunk(b"tEXt", b"Author\x00someone") + body,
                 "xmp.png": head + chunk(b"iTXt", b"XML:com.adobe.xmp\x00\x00\x00\x00\x00<x/>") + body,
                 "exif.png": head + chunk(b"eXIf", b"MM\x00*") + body, "tail.png": head + body + b"extra",
                 "broken.png": (head + body)[:-3]}
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            (root / "assets/shots").mkdir(parents=True)
            for name, data in cases.items():
                (root / "assets/shots" / name).write_bytes(data)
            found = [p for p in checks.run(root) if "assets/" in p]
            self.assertEqual(sorted(found), [
                "hygiene: assets/shots/broken.png is a malformed PNG (truncated chunk)",
                "hygiene: assets/shots/exif.png has PNG metadata chunks ['eXIf']",
                "hygiene: assets/shots/tail.png has 5 bytes after IEND",
                "hygiene: assets/shots/text.png has PNG metadata chunks ['tEXt']",
                "hygiene: assets/shots/xmp.png has PNG metadata chunks ['iTXt']"])
            self.assertNotIn("someone", "\n".join(found))

    def test_min_version_must_equal_the_manifest_floor(self):
        from umber import registry
        base = dict(name="x", category="editor", phase=1, docs="internal", format_confirmed=True, target_version="1",
                    install="i", uninstall="u", checklist=("c",))
        files = {"vscode": ("package.json", '{"engines": {"vscode": "^1.95.0"}}'),
                 "jetbrains": ("META-INF/plugin.xml", '<idea-plugin><idea-version since-build="243"/></idea-plugin>'),
                 "obsidian": ("manifest.json", '{"minAppVersion": "1.7.0"}')}
        good = {"vscode": "1.95.0", "jetbrains": "2024.3", "obsidian": "1.7.0"}
        with tempdir() as d:
            root = Path(d)
            for pid, (rel, text) in files.items():
                (root / f"ports/{pid}" / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / f"ports/{pid}" / rel).write_text(text, encoding="utf-8")
            ports = [registry.Port(id=pid, output_root=f"ports/{pid}", min_version=v, **base) for pid, v in good.items()]
            self.assertEqual(checks.manifest_floor_problems(root, ports), [])
            bad = [registry.Port(id=pid, output_root=f"ports/{pid}", min_version="9.9", **base) for pid in good]
            bad.append(registry.Port(id="kitty", output_root="ports/kitty", min_version="0.35", **base))
            bad.append(registry.Port(id="vscode", output_root="ports/vscode", **base))
            found = checks.manifest_floor_problems(root, bad)
            for needle in ("vscode: min_version '9.9' is not the manifest floor '1.95.0'",
                           "jetbrains: min_version '9.9' is not the manifest floor '2024.3'",
                           "obsidian: min_version '9.9' is not the manifest floor '1.7.0'",
                           "kitty: min_version is set but the port ships no manifest that declares a floor",
                           "vscode: min_version '' is not the manifest floor '1.95.0'"):
                self.assertTrue(any(needle in f for f in found), (needle, found))
        self.assertEqual(checks.manifest_floor_problems(REPO, registry.load_ports(REPO / "ports.toml")), [])

    def test_invalid_verification_record_is_reported(self):
        with tempdir() as d:
            root = fixture(d); buildcmd.build(root)
            (root / "verifications.json").write_text('{"demo": [{"status": "verified"}]}', encoding="utf-8")
            self.assertTrue(checks.run(root)[0].startswith("config: verifications.json"))

if __name__ == "__main__":
    unittest.main()
