"""Release artifacts (spec §14): reproducible archives, the .vsix and SHA256SUMS. Standard library only."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from . import buildcmd, palette, registry, safepath

FIXED_TIME = (1980, 1, 1, 0, 0, 0)
ARCHIVE_SUFFIX = {"jetbrains": "jar", "firefox": "xpi"}
PREFIX = {"obsidian": "Umber Calm/"}
SUMS = "SHA256SUMS"
CONTENT_TYPES = ('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Default Extension=".json" ContentType="application/json"/>'
                 '<Default Extension=".md" ContentType="text/markdown"/>'
                 '<Default Extension=".txt" ContentType="text/plain"/>'
                 '<Default Extension=".vsixmanifest" ContentType="text/xml"/>'
                 '</Types>\n')


class PackageError(ValueError):
    pass


@dataclass(frozen=True)
class Artifact:
    name: str
    kind: str
    port: str


def inventory(root: Path, ports: list[registry.Port]) -> list[Artifact]:
    version = palette.load(Path(root) / "palette" / "umber-calm.toml").meta["release"]
    items = []
    for p in sorted(ports, key=lambda p: p.id):
        items.append(Artifact(f"umber-calm-{p.id}-{version}.zip", "zip", p.id))
        if p.id in ARCHIVE_SUFFIX:
            kind = ARCHIVE_SUFFIX[p.id]
            items.append(Artifact(f"umber-calm-{p.id}-{version}.{kind}", kind, p.id))
        if p.id == "vscode":
            items.append(Artifact(f"umber-calm-{version}.vsix", "vsix", p.id))
        if p.id == "json":
            items.append(Artifact("umber-calm.json", "json", p.id))
    return items


def sha256sums(paths: list[Path]) -> str:
    return "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n"
                   for p in sorted(paths, key=lambda p: p.name))


def _write_zip(target: Path, members: list[tuple[str, bytes]]) -> None:
    names = [n for n, _ in members]
    if len(names) != len(set(names)):
        raise PackageError(f"{target.name}: duplicate archive entries")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_STORED) as z:
        for name, data in sorted(members):
            info = zipfile.ZipInfo(name, date_time=FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, data)


def _reset(out: Path) -> None:
    if out.exists():
        foreign = sorted(p.name for p in out.iterdir()
                         if not (p.is_file() and (p.name == SUMS or p.name.startswith("umber-calm"))))
        if foreign:
            raise PackageError(f"{out} contains files package.py did not create: {foreign}; refusing to delete them")
        shutil.rmtree(out)
    out.mkdir(parents=True)


def _port_files(root: Path, port: registry.Port, inputs: list[str]) -> list[tuple[str, bytes]]:
    if not inputs:
        raise PackageError(f"port {port.id!r} has no files to package")
    own = f"ports/{port.id}/"
    base = own if port.output_root == "." else port.output_root.rstrip("/") + "/"
    files = []
    for rel in inputs:
        if port.output_root == ".":
            name = rel[len(own):] if rel.startswith(own) else rel
        else:
            name = rel[len(base):] if rel.startswith(base) else Path(rel).name
        files.append((name, safepath.read_bytes(root, rel)))
    readme = safepath.inside(root, own + "README.md")
    if readme.is_file():
        files.append(("README.md", readme.read_bytes()))
    return files


def _vsixmanifest(pkg: dict) -> str:
    def e(value) -> str:
        return escape(str(value), {'"': "&quot;"})
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" '
            'xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">\n'
            "  <Metadata>\n"
            f'    <Identity Language="en-US" Id="{e(pkg["name"])}" Version="{e(pkg["version"])}" '
            f'Publisher="{e(pkg["publisher"])}"/>\n'
            f"    <DisplayName>{e(pkg['displayName'])}</DisplayName>\n"
            f'    <Description xml:space="preserve">{e(pkg["description"])}</Description>\n'
            f"    <Tags>{e(','.join(pkg.get('keywords', [])))}</Tags>\n"
            f"    <Categories>{e(','.join(pkg.get('categories', [])))}</Categories>\n"
            "    <GalleryFlags>Public</GalleryFlags>\n"
            "    <Properties>\n"
            f'      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{e(pkg["engines"]["vscode"])}"/>\n'
            '      <Property Id="Microsoft.VisualStudio.Code.ExtensionDependencies" Value=""/>\n'
            '      <Property Id="Microsoft.VisualStudio.Code.ExtensionPack" Value=""/>\n'
            '      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="ui,workspace"/>\n'
            '      <Property Id="Microsoft.VisualStudio.Code.LocalizedLanguages" Value=""/>\n'
            f'      <Property Id="Microsoft.VisualStudio.Services.Links.Source" Value="{e(pkg["repository"]["url"])}"/>\n'
            "    </Properties>\n"
            "    <License>extension/LICENSE.txt</License>\n"
            "  </Metadata>\n"
            '  <Installation>\n    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>\n  </Installation>\n'
            "  <Dependencies/>\n"
            "  <Assets>\n"
            '    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>\n'
            '    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" '
            'Addressable="true"/>\n'
            '    <Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE.txt" '
            'Addressable="true"/>\n'
            "  </Assets>\n"
            "</PackageManifest>\n")


def _write_vsix(target: Path, files: list[tuple[str, bytes]], license_bytes: bytes) -> None:
    by_name = dict(files)
    for required in ("package.json", "README.md"):
        if required not in by_name:
            raise PackageError(f"vsix: ports/vscode/{required} is missing (run tools/build.py)")
    pkg = json.loads(by_name["package.json"])
    members = [("[Content_Types].xml", CONTENT_TYPES.encode("utf-8")),
               ("extension.vsixmanifest", _vsixmanifest(pkg).encode("utf-8")),
               ("extension/LICENSE.txt", license_bytes)]
    members += [(f"extension/{name}", data) for name, data in files]
    _write_zip(target, members)


def package(root: Path, out_dir: Path) -> list[Path]:
    root, out = Path(root), Path(out_dir)
    stale = buildcmd.stale(root)
    if stale:
        raise PackageError(f"generated files are stale, run tools/build.py first: {stale[:10]}")
    ports = {p.id: p for p in registry.load_ports(root / "ports.toml")}
    states = buildcmd.states(root)
    wanted = inventory(root, list(ports.values()))
    license_bytes = safepath.read_bytes(root, "LICENSE")
    _reset(out)
    made: list[Path] = []
    for art in wanted:
        port, target = ports[art.port], out / art.name
        files = _port_files(root, port, list(states[port.id].inputs))
        if art.kind == "zip":
            prefix = PREFIX.get(port.id, "")
            _write_zip(target, [(prefix + n, d) for n, d in files] + [(prefix + "LICENSE", license_bytes)])
        elif art.kind in ("jar", "xpi"):
            _write_zip(target, [(n, d) for n, d in files if n != "README.md"] + [("LICENSE", license_bytes)])
        elif art.kind == "vsix":
            _write_vsix(target, files, license_bytes)
        else:
            target.write_bytes(safepath.read_bytes(root, f"{port.output_root}/umber-calm.json"))
        made.append(target)
    sums = out / SUMS
    sums.write_bytes(sha256sums(made).encode("utf-8"))
    return made + [sums]
