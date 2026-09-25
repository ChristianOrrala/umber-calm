"""All repository checks (spec §8.1). run() returns a list of problems; empty means pass."""
from __future__ import annotations

import json
import plistlib
import re
import subprocess
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

from . import outputs, palette, readability, registry, safepath, structure, syntaxcheck, template
from .hygiene import line_of as _line, png_problems, scan_text

UNRESOLVED = re.compile(r"\{\{\s*[A-Za-z]")
ESCAPE = re.compile(r"""\{\{\s*(["'])\{\{\1\s*\}\}""")
SYNTAX_REF = re.compile(r"\{\{[^}]*?\bsyntax\.[a-z_]+")
WORDING_PATTERNS = [
    ("health or outcome claim", re.compile(r"\b(?:reduc|prevent|reliev|eas|cur|heal|treat|protect)\w*\s+(?:\w+\s+){0,3}"
                                 r"(?:eye\s*strain|strain|fatigue|headaches?|pain|symptoms?|sensitivity)\b", re.I)),
    ("health or outcome claim", re.compile(r"\b(?:safe|easy|gentle)\s+(?:on|for)\s+(?:\w+\s+)?eyes\b", re.I)),
]
WORDING_EXEMPT = ("CONTRIBUTING.md",)  # defines the rule, so it quotes what is not allowed
RESERVED_TOP = ("plugin", "ftplugin", "syntax", "after", "indent", "queries", "autoload", "spell", "pack", "compiler")
ASSET_BUDGET = 5 * 1024 * 1024
XML_SUFFIXES = (".xml", ".icls", ".tmtheme", ".svg")
USES = re.compile(r"^\s*-?\s*uses:\s*[\"']?([^\"'\s#]+)[\"']?\s*(#.*)?$")


def _tracked_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
        names = [n for n in out.decode("utf-8").split("\0") if n]
        if names:
            return [root / n for n in names if (root / n).is_file()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts]


JSON_SUFFIXES = (".json", ".sublime-color-scheme")
PARSED_SUFFIXES = JSON_SUFFIXES + (".toml", ".plist", ".itermcolors") + XML_SUFFIXES


def _parse_problems(rel: str, data: bytes) -> list[str]:
    """Standard-library parse of JSON, TOML, plist and XML outputs."""
    lower = rel.lower()
    try:
        if lower.endswith(JSON_SUFFIXES):
            json.loads(data.decode("utf-8"))
        elif lower.endswith(".toml"):
            tomllib.loads(data.decode("utf-8"))
        elif lower.endswith((".plist", ".itermcolors")):
            plistlib.loads(data)
        elif lower.endswith(XML_SUFFIXES):
            ET.fromstring(data)
    except Exception as e:  # noqa: BLE001 — report any parser failure
        return [f"format: {rel} does not parse: {e}"]
    return []


def _format_problems_text(rel: str, text: str) -> list[str]:
    return _parse_problems(rel, text.encode("utf-8"))


def _format_problems(root: Path, rel: str) -> list[str]:
    data = safepath.read_bytes(root, rel)
    found = _parse_problems(rel, data)
    if found:
        return found
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return []
    return structure.problems(root, rel, text)


def _templates(root: Path, port: registry.Port) -> list[tuple[str, str, str]]:
    """(template source path, output path, template text) for every .tmpl file of a port."""
    base = root / "templates" / port.id
    result = []
    for src in sorted(base.rglob("*.tmpl")) if base.is_dir() else []:
        rel_t = src.relative_to(base).as_posix()[: -len(".tmpl")]
        out = (PurePosixPath(port.output_root) / rel_t).as_posix()
        result.append((f"templates/{port.id}/{rel_t}.tmpl", out, src.read_text(encoding="utf-8")))
    return result


def _vscode_floor(data: bytes) -> str:
    return re.sub(r"^[\^~>=]+", "", json.loads(data)["engines"]["vscode"])


def _jetbrains_floor(data: bytes) -> str:
    build = ET.fromstring(data).find("idea-version").get("since-build")  # e.g. 243 or 243.12 -> 2024.3
    major, minor = build.split(".")[0][:2], build.split(".")[0][2:]
    return f"20{major}.{minor}"


def _obsidian_floor(data: bytes) -> str:
    return json.loads(data)["minAppVersion"]


# Port id -> (manifest file under output_root, reader of the floor it declares). spec §7.1 / §8.1 item 4.
MANIFEST_FLOORS = {"vscode": ("package.json", _vscode_floor), "jetbrains": ("META-INF/plugin.xml", _jetbrains_floor),
                   "obsidian": ("manifest.json", _obsidian_floor)}


def manifest_floor_problems(root: Path, ports: list[registry.Port]) -> list[str]:
    """`min_version` equals the lowest version the port's shipped manifest declares, and is set only where one does."""
    found = []
    for p in ports:
        if p.id not in MANIFEST_FLOORS:
            if p.min_version:
                found.append(f"registry: {p.id}: min_version is set but the port ships no manifest that declares a floor")
            continue
        rel, reader = MANIFEST_FLOORS[p.id]
        try:
            floor = reader(safepath.read_bytes(root, f"{p.output_root}/{rel}"))
        except (OSError, ValueError, KeyError, AttributeError, TypeError, ET.ParseError) as e:
            found.append(f"registry: {p.id}: cannot read the version floor from {rel}: {type(e).__name__}")
            continue
        if floor != p.min_version:
            found.append(f"registry: {p.id}: min_version {p.min_version!r} is not the manifest floor {floor!r}")
    return found


def _slug(heading: str) -> str:
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", heading.strip().lower()))


def _readme_problems(root: Path) -> list[str]:
    path = root / "README.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    anchors = {_slug(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.+)$", text, re.M)}
    return [f"readme: link #{a} has no matching heading" for a in re.findall(r"\]\(#([^)]+)\)", text) if a not in anchors]


def _workflow_problems(root: Path) -> list[str]:
    found = []
    wdir = root / ".github" / "workflows"
    for path in sorted(wdir.glob("*.y*ml")) if wdir.is_dir() else []:
        rel, text = path.relative_to(root).as_posix(), path.read_text(encoding="utf-8")
        for n, line in enumerate(text.splitlines(), 1):
            m = USES.match(line)
            if not m or m.group(1).startswith(("./", "docker://")):
                continue
            if not re.fullmatch(r"[^@]+@[0-9a-f]{40}", m.group(1)) or not m.group(2):
                found.append(f"workflow: {rel}:{n}: pin actions to a full commit SHA with a '# vX.Y.Z' comment")
        if text.count("actions/checkout@") != text.count("persist-credentials: false"):
            found.append(f"workflow: {rel}: every actions/checkout step needs persist-credentials: false")
    return found


def _hygiene_problems(root: Path) -> list[str]:
    found = [f"layout: top-level directory {name}/ is reserved (spec §3)" for name in RESERVED_TOP if (root / name).is_dir()]
    assets = root / "assets"
    if assets.is_dir():
        size = sum(p.stat().st_size for p in assets.rglob("*") if p.is_file())
        if size > ASSET_BUDGET:
            found.append(f"layout: assets/ is {size / 1048576:.1f} MB, over the 5 MB asset budget")
        for png in sorted(p for p in assets.rglob("*") if p.is_file() and p.suffix.lower() == ".png"):
            found += png_problems(png.read_bytes(), png.relative_to(root).as_posix())
    return found


def run(root: Path) -> list[str]:
    root = Path(root)
    found: list[str] = []
    try:
        pal = palette.load(safepath.inside(root, "palette/umber-calm.toml"))
        ports = registry.load_ports(safepath.inside(root, "ports.toml"))
        records = registry.load_verifications(safepath.inside(root, "verifications.json"))
        manifest = outputs.read_manifest(root)
    except (palette.PaletteError, registry.RegistryError, outputs.BuildError, safepath.UnsafePathError) as e:
        return [f"config: {e}"]
    found += readability.problems(pal)

    ids = {p.id for p in ports}
    tdir = root / "templates"
    dirs = {d.name for d in tdir.iterdir() if d.is_dir()} if tdir.is_dir() else set()
    found += [f"registry: port {m!r} has no templates/ directory" for m in sorted(ids - dirs)]
    found += [f"registry: templates/{e} has no ports.toml entry" for e in sorted(dirs - ids)]
    found += [f"registry: verifications.json references unknown port {pid!r}" for pid in records if pid not in ids]

    escaped: set[str] = set()
    measured = readability.measured_blends(pal)
    for port in ports:
        try:
            registry.digest_paths(root, port, [r for r, pid in manifest.items() if pid == port.id])
        except (registry.RegistryError, safepath.UnsafePathError) as e:
            found.append(f"registry: {e}")
        uses_syntax = False
        for source, out, text in _templates(root, port):
            if ESCAPE.search(text):
                escaped.add(out)
            uses_syntax = uses_syntax or bool(SYNTAX_REF.search(text))
            try:
                for line, hx in template.blends(text, pal, source=source):
                    if hx not in measured:
                        found.append(f"readability: {source}:{line}: blend result {hx} is not a measured state (spec §4.4)")
            except template.TemplateError as e:
                found.append(f"template: {e}")
        if (uses_syntax or port.category == "editor") and not (port.syntax_check or port.syntax_exempt):
            found.append(f"roles: port {port.id!r} maps syntax roles but declares neither syntax_check nor syntax_exempt")

    for rel in sorted(manifest):
        path = root / rel
        if not path.exists():
            found.append(f"output: {rel} is in the manifest but missing (run tools/build.py)")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if rel not in escaped and UNRESOLVED.search(text):
            found.append(f"output: unresolved expression in {rel}")
        found += _format_problems(root, rel)

    reserved = {name: pal.colors[name] for name in palette.RESERVED_SYNTAX}
    for p in ports:
        if p.syntax_check is None:
            continue
        path = root / p.output_root / p.syntax_check["file"]
        if not path.exists():
            found.append(f"syntax: {p.id}: {p.syntax_check['file']} not found (run tools/build.py)")
            continue
        found += [f"syntax: {p.id}: {v}" for v in syntaxcheck.violations(p.syntax_check["format"], path, reserved)]

    found += manifest_floor_problems(root, ports)
    found += _hygiene_problems(root) + _readme_problems(root) + _workflow_problems(root)

    for path in _tracked_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        found += scan_text(text, rel)
        if rel.endswith(".md") and rel not in WORDING_EXEMPT:
            for label, pattern in WORDING_PATTERNS:
                found += [f"wording: {label} in {rel}:{_line(text, m.start())} (spec §11.2)" for m in pattern.finditer(text)]
    return found
