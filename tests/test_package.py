import hashlib, re, struct, unittest, zipfile, zlib
import xml.etree.ElementTree as ET
from pathlib import Path
from tests.helpers import tempdir
from tests.test_buildcmd import fixture
from umber import buildcmd, package, palette, registry

EXTRA = '''
[[port]]
id = "jetbrains"
name = "JetBrains"
category = "editor"
phase = 2
output_root = "ports/jetbrains"
docs = "internal"
format_confirmed = true
target_version = "2024.3"
install = "Install from disk."
uninstall = "Uninstall the plugin."
checklist = ["editor background"]

[[port]]
id = "vscode"
name = "VS Code"
category = "editor"
phase = 1
output_root = "ports/vscode"
docs = "internal"
format_confirmed = true
target_version = "1.95"
install = "Install the vsix."
uninstall = "Uninstall the extension."
checklist = ["editor background"]
inputs = ["assets/marketplace/icon.png"]
'''
PKG = ('{"name": "umber-calm", "displayName": "Umber Calm", "description": "A warm palette.", '
       '"version": "{{ meta.release }}", "publisher": "umber-calm", "engines": {"vscode": "^1.95.0"}, '
       '"categories": ["Themes"], "keywords": ["theme"], "repository": {"type": "git", "url": "{{ meta.homepage }}"}, '
       '"icon": "icon.png", "galleryBanner": {"color": "{{ ui.bg }}", "theme": "dark"}, "homepage": "{{ meta.homepage }}", '
       '"bugs": {"url": "{{ meta.homepage }}/issues"}, "qna": "{{ meta.homepage }}/issues", '
       '"contributes": {"themes": [{"label": "Umber Calm", "uiTheme": "vs-dark", "path": "./themes/t.json"}]}}\n')
FIXED = (1980, 1, 1, 0, 0, 0)
PAGE = b"# Listing page\n"
CHANGELOG = b"# Changelog\n"
NS = {"v": "http://schemas.microsoft.com/developer/vsx-schema/2011"}

def tiny_png() -> bytes:
    """A valid 1x1 PNG with no metadata chunks."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\x20\x1f\x1d")) + chunk(b"IEND", b""))

def repo(d, release="9.9.9") -> Path:
    root = fixture(d)
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    pal = root / "palette/umber-calm.toml"
    text, n = re.subn(r'^release = ".*"$', f'release = "{release}"', pal.read_text(encoding="utf-8"), flags=re.M)
    assert n == 1, "palette has no [meta] release line"
    pal.write_text(text, encoding="utf-8", newline="\n")
    with open(root / "ports.toml", "a", encoding="utf-8") as f:
        f.write(EXTRA)
    (root / "templates/jetbrains/META-INF").mkdir(parents=True)
    (root / "templates/jetbrains/META-INF/plugin.xml.tmpl").write_text("<idea-plugin/>\n", encoding="utf-8")
    (root / "templates/vscode/themes").mkdir(parents=True)
    (root / "templates/vscode/package.json.tmpl").write_text(PKG, encoding="utf-8")
    (root / "templates/vscode/themes/t.json.tmpl").write_text('{"colors": {"editor.background": "{{ bg }}"}}\n',
                                                              encoding="utf-8")
    (root / "assets/marketplace").mkdir(parents=True)
    (root / "assets/marketplace/icon.png").write_bytes(tiny_png())
    (root / "docs/marketplace").mkdir(parents=True)
    (root / "docs/marketplace/vscode.md").write_bytes(PAGE)
    (root / "CHANGELOG.md").write_bytes(CHANGELOG)
    buildcmd.build(root)
    return root

class PackageTest(unittest.TestCase):
    def test_inventory_and_contents(self):
        with tempdir() as d:
            root = repo(d)
            made = package.package(root, root / "dist")
            names = [p.name for p in made]
            ports = registry.load_ports(root / "ports.toml")
            self.assertEqual(names, [a.name for a in package.inventory(root, ports)] + ["SHA256SUMS"])
            self.assertIn("umber-calm-demo-9.9.9.zip", names)
            self.assertIn("umber-calm-jetbrains-9.9.9.jar", names)
            self.assertIn("umber-calm-9.9.9.vsix", names)
            with zipfile.ZipFile(root / "dist/umber-calm-demo-9.9.9.zip") as z:
                self.assertEqual(z.namelist(), ["LICENSE", "README.md", "demo.conf"])
            with zipfile.ZipFile(root / "dist/umber-calm-jetbrains-9.9.9.jar") as z:
                self.assertEqual(z.namelist(), ["LICENSE", "META-INF/plugin.xml"])
            with zipfile.ZipFile(root / "dist/umber-calm-9.9.9.vsix") as z:
                self.assertEqual(z.namelist(), ["[Content_Types].xml", "extension.vsixmanifest", "extension/CHANGELOG.md",
                                                "extension/LICENSE.txt", "extension/README.md", "extension/icon.png",
                                                "extension/package.json", "extension/themes/t.json"])
                manifest = ET.fromstring(z.read("extension.vsixmanifest"))
            ns = {"v": "http://schemas.microsoft.com/developer/vsx-schema/2011"}
            identity = manifest.find("v:Metadata/v:Identity", ns)
            self.assertEqual((identity.get("Id"), identity.get("Version"), identity.get("Publisher")),
                             ("umber-calm", "9.9.9", "umber-calm"))
            for path in made[:-1]:
                with zipfile.ZipFile(path) as z:
                    self.assertTrue({"LICENSE", "extension/LICENSE.txt"} & set(z.namelist()), path.name)

    def test_json_port_attaches_the_raw_export(self):
        with tempdir() as d:
            root = repo(d)
            demo = registry.load_ports(root / "ports.toml")[0]
            json_port = registry.Port(**{**demo.__dict__, "id": "json", "output_root": "ports/json"})
            kinds = {(a.name, a.kind) for a in package.inventory(root, [json_port])}
            self.assertEqual(kinds, {("umber-calm-json-9.9.9.zip", "zip"), ("umber-calm.json", "json")})

    def test_version_comes_from_the_palette(self):
        with tempdir() as d:
            root = repo(d, release="0.2.0")
            self.assertIn("umber-calm-demo-0.2.0.zip", [p.name for p in package.package(root, root / "dist")])

    def test_reproducible_and_normalized(self):
        with tempdir() as d:
            root = repo(d)
            first = package.package(root, root / "a")
            second = package.package(root, root / "b")
            for a, b in zip(first, second):
                self.assertEqual(a.read_bytes(), b.read_bytes(), a.name)
            for path in first[:-1]:
                with zipfile.ZipFile(path) as z:
                    self.assertEqual(z.comment, b"")
                    self.assertEqual(z.namelist(), sorted(z.namelist()))
                    for info in z.infolist():
                        self.assertEqual((info.date_time, info.create_system, info.external_attr, info.extra,
                                          info.comment, info.compress_type),
                                         (FIXED, 3, 0o644 << 16, b"", b"", zipfile.ZIP_STORED), info.filename)

    def test_sha256sums(self):
        with tempdir() as d:
            root = repo(d)
            made = package.package(root, root / "dist")
            lines = (root / "dist/SHA256SUMS").read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines, [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}"
                                     for p in sorted(made[:-1], key=lambda p: p.name)])

    def test_output_directory_is_rebuilt_but_foreign_files_are_refused(self):
        with tempdir() as d:
            root = repo(d)
            out = root / "dist"
            out.mkdir()
            (out / "umber-calm-old-0.0.1.zip").write_bytes(b"old")
            package.package(root, out)
            self.assertFalse((out / "umber-calm-old-0.0.1.zip").exists())
            (out / "notes.txt").write_text("mine", encoding="utf-8")
            with self.assertRaisesRegex(package.PackageError, "notes.txt"):
                package.package(root, out)

    def test_refuses_stale_outputs(self):
        with tempdir() as d:
            root = repo(d)
            (root / "templates/demo/demo.conf.tmpl").write_text("bg={{ surface }}\n", encoding="utf-8")
            with self.assertRaisesRegex(package.PackageError, "stale"):
                package.package(root, root / "dist")

class VsixListingTest(unittest.TestCase):
    def vsix(self, root):
        package.package(root, root / "dist")
        return zipfile.ZipFile(root / "dist/umber-calm-9.9.9.vsix")

    def test_vsix_carries_the_listing_page_changelog_and_icon(self):
        with tempdir() as d:
            root = repo(d)
            with self.vsix(root) as z:
                self.assertEqual(z.read("extension/README.md"), PAGE)
                self.assertEqual(z.read("extension/CHANGELOG.md"), CHANGELOG)
                self.assertEqual(z.read("extension/icon.png"), tiny_png())
                self.assertIn('<Default Extension=".png" ContentType="image/png"/>', z.read("[Content_Types].xml").decode())

    def test_vsix_manifest_has_the_listing_fields(self):
        with tempdir() as d:
            root = repo(d)
            home = palette.load(root / "palette/umber-calm.toml").meta["homepage"]
            bg = palette.load(root / "palette/umber-calm.toml").resolve("ui.bg")
            with self.vsix(root) as z:
                manifest = ET.fromstring(z.read("extension.vsixmanifest"))
            props = {p.get("Id").removeprefix("Microsoft.VisualStudio."): p.get("Value")
                     for p in manifest.findall("v:Metadata/v:Properties/v:Property", NS)}
            self.assertEqual({k: props.get(k) for k in (
                "Services.Branding.Color", "Services.Branding.Theme", "Services.Links.Source",
                "Services.Links.Getstarted", "Services.Links.GitHub", "Services.Links.Support", "Services.Links.Learn",
                "Services.CustomerQnALink", "Services.GitHubFlavoredMarkdown", "Services.Content.Pricing",
                "Code.EnabledApiProposals")},
                {"Services.Branding.Color": bg, "Services.Branding.Theme": "dark", "Services.Links.Source": home,
                 "Services.Links.Getstarted": home, "Services.Links.GitHub": home,
                 "Services.Links.Support": f"{home}/issues", "Services.Links.Learn": home,
                 "Services.CustomerQnALink": f"{home}/issues", "Services.GitHubFlavoredMarkdown": "true",
                 "Services.Content.Pricing": "Free", "Code.EnabledApiProposals": ""})
            self.assertEqual(manifest.find("v:Metadata/v:Icon", NS).text, "extension/icon.png")
            assets = {(a.get("Type"), a.get("Path")) for a in manifest.findall("v:Assets/v:Asset", NS)}
            self.assertEqual(assets, {
                ("Microsoft.VisualStudio.Code.Manifest", "extension/package.json"),
                ("Microsoft.VisualStudio.Services.Content.Details", "extension/README.md"),
                ("Microsoft.VisualStudio.Services.Content.Changelog", "extension/CHANGELOG.md"),
                ("Microsoft.VisualStudio.Services.Content.License", "extension/LICENSE.txt"),
                ("Microsoft.VisualStudio.Services.Icons.Default", "extension/icon.png")})

    def test_theme_only_vsix_is_a_web_extension_like_vsce_makes_it(self):
        # vscode.dev (the listing's "try it in your browser" link) only loads web extensions; vsce marks an extension
        # without code as one and tags color themes.
        with tempdir() as d:
            root = repo(d)
            with self.vsix(root) as z:
                manifest = ET.fromstring(z.read("extension.vsixmanifest"))
            kind = [p.get("Value") for p in manifest.findall("v:Metadata/v:Properties/v:Property", NS)
                    if p.get("Id") == "Microsoft.VisualStudio.Code.ExtensionKind"]
            self.assertEqual(kind, ["ui,workspace,web"])
            tags = manifest.find("v:Metadata/v:Tags", NS).text.split(",")
            self.assertLessEqual({"theme", "color-theme", "__web_extension"}, set(tags))
            self.assertEqual(len(tags), len(set(tags)))

    def test_vsix_refuses_a_missing_marketplace_page(self):
        with tempdir() as d:
            root = repo(d)
            (root / "docs/marketplace/vscode.md").unlink()
            with self.assertRaisesRegex(package.PackageError, "docs/marketplace/vscode.md is missing"):
                package.package(root, root / "dist")

    def test_vsix_refuses_missing_named_files(self):
        with tempdir() as d:
            root = repo(d)
            text = (root / "ports.toml").read_text(encoding="utf-8")
            (root / "ports.toml").write_text(text.replace('inputs = ["assets/marketplace/icon.png"]\n', ""),
                                             encoding="utf-8")
            buildcmd.build(root)
            with self.assertRaisesRegex(package.PackageError, "package.json names icon.png, which is not packaged"):
                package.package(root, root / "dist")

if __name__ == "__main__":
    unittest.main()
