"""Release artifacts (spec §14): reproducible archives, the .vsix and SHA256SUMS. Standard library only."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from . import buildcmd, marketplace, palette, registry, safepath

FIXED_TIME = (1980, 1, 1, 0, 0, 0)
ARCHIVE_SUFFIX = {"jetbrains": "jar", "firefox": "xpi"}
PREFIX = {"obsidian": "Umber Calm/"}
VSIX = {"vscode": "umber-calm-{version}.vsix", "kiro": "umber-calm-kiro-{version}.vsix"}
SUMS = "SHA256SUMS"
CONTENT_TYPES = ('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Default Extension=".json" ContentType="application/json"/>'
                 '<Default Extension=".md" ContentType="text/markdown"/>'
                 '<Default Extension=".png" ContentType="image/png"/>'
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
        if p.id in VSIX:
            items.append(Artifact(VSIX[p.id].format(version=version), "vsix", p.id))
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


def _vsixmanifest(pkg: dict, names: set[str]) -> str:
    """The manifest the Marketplace reads the listing from, with the properties and assets `vsce` writes
    (vsce src/package.ts, toVsixManifest), so a hand-built .vsix lists the same fields."""
    def e(value) -> str:
        return escape(str(value), {'"': "&quot;"})

    def prop(pid: str, value) -> str:
        return f'      <Property Id="Microsoft.VisualStudio.{pid}" Value="{e(value)}"/>\n'

    web = "main" not in pkg and "browser" not in pkg  # no code to run: vsce marks it a web extension (vscode.dev)
    tags = list(pkg.get("keywords", []))
    if pkg.get("contributes", {}).get("themes"):
        tags += ["theme", "color-theme"]
    if web:
        tags.append("__web_extension")
    props = [prop("Code.Engine", pkg["engines"]["vscode"]), prop("Code.ExtensionDependencies", ""),
             prop("Code.ExtensionPack", ""), prop("Code.ExtensionKind", "ui,workspace,web" if web else "ui,workspace"),
             prop("Code.LocalizedLanguages", ""), prop("Code.EnabledApiProposals", "")]
    repo = pkg.get("repository", {}).get("url")
    if repo:
        props += [prop("Services.Links.Source", repo), prop("Services.Links.Getstarted", repo),
                  prop("Services.Links.GitHub" if "github.com" in repo else "Services.Links.Repository", repo)]
    if pkg.get("bugs", {}).get("url"):
        props.append(prop("Services.Links.Support", pkg["bugs"]["url"]))
    if pkg.get("homepage"):
        props.append(prop("Services.Links.Learn", pkg["homepage"]))
    banner = pkg.get("galleryBanner", {})
    if banner.get("color"):
        props.append(prop("Services.Branding.Color", banner["color"]))
    if banner.get("theme"):
        props.append(prop("Services.Branding.Theme", banner["theme"]))
    props += [prop("Services.GitHubFlavoredMarkdown", "false" if pkg.get("markdown") == "standard" else "true"),
              prop("Services.Content.Pricing", pkg.get("pricing", "Free"))]
    qna = pkg.get("qna")
    if qna == "marketplace" or qna is False:
        props.append(prop("Services.EnableMarketplaceQnA", "true" if qna else "false"))
    elif isinstance(qna, str):
        props.append(prop("Services.CustomerQnALink", qna))
    icon = f"extension/{pkg['icon']}" if pkg.get("icon") else ""
    assets = [("Code.Manifest", "extension/package.json"), ("Services.Content.Details", "extension/README.md")]
    if "CHANGELOG.md" in names:
        assets.append(("Services.Content.Changelog", "extension/CHANGELOG.md"))
    assets.append(("Services.Content.License", "extension/LICENSE.txt"))
    if icon:
        assets.append(("Services.Icons.Default", icon))
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" '
            'xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">\n'
            "  <Metadata>\n"
            f'    <Identity Language="en-US" Id="{e(pkg["name"])}" Version="{e(pkg["version"])}" '
            f'Publisher="{e(pkg["publisher"])}"/>\n'
            f"    <DisplayName>{e(pkg['displayName'])}</DisplayName>\n"
            f'    <Description xml:space="preserve">{e(pkg["description"])}</Description>\n'
            f"    <Tags>{e(','.join(dict.fromkeys(tags)))}</Tags>\n"
            f"    <Categories>{e(','.join(pkg.get('categories', [])))}</Categories>\n"
            "    <GalleryFlags>Public</GalleryFlags>\n"
            "    <Properties>\n" + "".join(props) + "    </Properties>\n"
            "    <License>extension/LICENSE.txt</License>\n"
            + (f"    <Icon>{e(icon)}</Icon>\n" if icon else "") +
            "  </Metadata>\n"
            '  <Installation>\n    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>\n  </Installation>\n'
            "  <Dependencies/>\n"
            "  <Assets>\n"
            + "".join(f'    <Asset Type="Microsoft.VisualStudio.{t}" Path="{e(path)}" Addressable="true"/>\n'
                      for t, path in assets) +
            "  </Assets>\n"
            "</PackageManifest>\n")


def _write_vsix(target: Path, port: registry.Port, files: list[tuple[str, bytes]], license_bytes: bytes,
                readme: bytes, changelog: bytes) -> None:
    """The port's files with its listing page as README.md (not the port README) and the changelog."""
    files = [(n, d) for n, d in files if n != "README.md"] + [("README.md", readme), ("CHANGELOG.md", changelog)]
    by_name = dict(files)
    if "package.json" not in by_name:
        raise PackageError(f"vsix: {port.output_root}/package.json is missing (run tools/build.py)")
    pkg = json.loads(by_name["package.json"])
    named = [pkg.get("icon")] + [t.get("path") for t in pkg.get("contributes", {}).get("themes", [])]
    for name in (n.removeprefix("./") for n in named if n):
        if name not in by_name:
            raise PackageError(f"vsix: {port.id}: package.json names {name}, which is not packaged")
    members = [("[Content_Types].xml", CONTENT_TYPES.encode("utf-8")),
               ("extension.vsixmanifest", _vsixmanifest(pkg, set(by_name)).encode("utf-8")),
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
            page = marketplace.PAGES[port.id]
            for rel in (page, "CHANGELOG.md"):
                if not (root / rel).is_file():
                    raise PackageError(f"vsix: {rel} is missing (run tools/build.py)")
            _write_vsix(target, port, files, license_bytes, safepath.read_bytes(root, page),
                        safepath.read_bytes(root, "CHANGELOG.md"))
        else:
            target.write_bytes(safepath.read_bytes(root, f"{port.output_root}/umber-calm.json"))
        made.append(target)
    sums = out / SUMS
    sums.write_bytes(sha256sums(made).encode("utf-8"))
    return made + [sums]
