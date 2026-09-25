"""Plan generated outputs from templates, validate every write and deletion, write them, keep the manifest."""
from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from . import safepath
from .palette import Palette
from .registry import Port
from .template import render

ALLOWED_ROOTS = ("ports/", "colors/umber-calm.vim", "lua/umber-calm/palette.lua",
                 "docs/color-vision.md", "docs/renders/")
MANIFEST = ".generated-manifest"
WINDOWS_INVALID = re.compile(r'[\x00-\x1f\x7f<>:"|?*]')  # control characters, Windows-invalid, stream colons
OWNER_RE = re.compile(r"(?:readme:)?[a-z0-9][a-z0-9-]*")
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


class BuildError(ValueError):
    pass


def validate_rel(rel: str) -> None:
    """Raise BuildError unless `rel` is a safe, portable, repository-relative path inside ALLOWED_ROOTS."""
    if not rel or "\\" in rel or rel.startswith("/") or re.match(r"[A-Za-z]:", rel):
        raise BuildError(f"unsafe output path {rel!r}: absolute, drive, UNC or backslash")
    if WINDOWS_INVALID.search(rel):
        raise BuildError(f"unsafe output path {rel!r}: control character or one of < > : \" | ? *")
    for segment in rel.split("/"):
        if segment in ("", ".", ".."):
            raise BuildError(f"unsafe output path {rel!r}: empty, '.' or '..' segment")
        if segment.split(".")[0].upper() in WINDOWS_RESERVED:
            raise BuildError(f"unsafe output path {rel!r}: Windows reserved name {segment!r}")
        if segment[-1] in ". ":
            raise BuildError(f"unsafe output path {rel!r}: segment ends with a dot or space")
    if not any(rel == a or (a.endswith("/") and rel.startswith(a)) for a in ALLOWED_ROOTS):
        raise BuildError(f"output {rel!r} is outside the allowed roots {ALLOWED_ROOTS}")


def is_allowed(rel: str) -> bool:
    try:
        validate_rel(rel)
    except BuildError:
        return False
    return True


def plan(root: Path, pal: Palette, ports: list[Port]) -> dict[str, tuple[str, bytes]]:
    tdir = Path(root) / "templates"
    dirs = {d.name for d in tdir.iterdir() if d.is_dir()} if tdir.is_dir() else set()
    ids = {p.id for p in ports}
    if ids - dirs:
        raise BuildError(f"ports without a templates/ directory: {sorted(ids - dirs)}")
    if dirs - ids:
        raise BuildError(f"templates/ directories without a ports.toml entry: {sorted(dirs - ids)}")
    result: dict[str, tuple[str, bytes]] = {}
    folded: dict[str, str] = {}
    for port in ports:
        base = tdir / port.id
        safepath.inside(root, f"templates/{port.id}")
        for src in sorted(base.rglob("*")):
            rel_t = src.relative_to(base).as_posix()
            source = f"templates/{port.id}/{rel_t}"
            safepath.inside(root, source)  # refuses symlinked template files and directories
            if src.is_dir():
                continue
            if src.suffix == ".tmpl":
                text = render(safepath.read_text(root, source), pal, source=source,
                              extra={"meta.template": source})
                content, rel_t = text.encode("utf-8"), rel_t[: -len(".tmpl")]
            else:
                content = safepath.read_bytes(root, source)
            out = (PurePosixPath(port.output_root) / rel_t).as_posix()
            try:
                validate_rel(out)
            except BuildError as e:
                raise BuildError(f"{port.id}: {e}") from None
            if out in result:
                raise BuildError(f"collision: {out!r} is produced by {result[out][0]!r} and {port.id!r}")
            if out.casefold() in folded:
                raise BuildError(f"collision: {out!r} and {folded[out.casefold()]!r} differ only by case")
            folded[out.casefold()] = out
            result[out] = (port.id, content)
    return result


def read_manifest(root: Path) -> dict[str, str]:
    """{rel path: owner}. Every line is exactly `<owner>\\t<path>`; anything else is an error naming the line."""
    path = safepath.inside(root, MANIFEST)
    if not path.exists():
        return {}
    entries: dict[str, str] = {}
    lines = path.read_bytes().decode("utf-8").split("\n")
    if lines[-1] == "":
        lines.pop()  # the final newline
    for n, line in enumerate(lines, 1):
        owner, tab, rel = line.partition("\t")
        if not tab or not OWNER_RE.fullmatch(owner) or not rel or "\t" in rel or "\r" in rel:
            raise BuildError(f"{MANIFEST}:{n}: malformed line (expected <owner><TAB><path>); run tools/build.py "
                             "after restoring it from git")
        if rel in entries:
            raise BuildError(f"{MANIFEST}:{n}: duplicate path")
        entries[rel] = owner
    return entries


def paths_by_port(planned: dict[str, tuple[str, bytes]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for rel, (pid, _) in planned.items():
        grouped.setdefault(pid, []).append(rel)
    return grouped


def stale(root: Path, planned: dict[str, tuple[str, bytes]]) -> list[str]:
    """Planned paths whose file is missing or differs from what the build would write. Writes nothing."""
    root = Path(root)
    return sorted(rel for rel, (_, content) in planned.items()
                  if not safepath.inside(root, rel).is_file() or (root / rel).read_bytes() != content)


def _check_destination(root: Path, rel: str) -> None:
    """A safe, allowed path with no symlink in any component, resolving inside the repository and outside .git."""
    validate_rel(rel)
    try:
        safepath.inside(root, rel)
    except safepath.UnsafePathError as e:
        raise BuildError(f"unsafe destination: {e}") from None


def preflight(root: Path, owners: dict[str, str]) -> list[str]:
    """Validate a complete destination set (rel path -> owner) and the deletions it implies. Writes nothing.

    Returns the orphans: previous manifest entries that are not destinations. An existing file that the
    previous manifest does not list is refused even when it is byte-identical: it is never adopted."""
    root = Path(root)
    previous = read_manifest(root)
    orphans = sorted(set(previous) - set(owners))
    _check_collisions(root, owners)
    for rel in orphans:
        try:
            _check_destination(root, rel)
        except BuildError as e:
            raise BuildError(f"manifest entry {rel!r} is unsafe ({e}); refusing to delete") from None
    for rel in sorted(owners):
        _check_destination(root, rel)
        if rel not in previous and (root / rel).exists():
            raise BuildError(f"refusing to overwrite unowned file {rel!r} (not in {MANIFEST}); move it away first")
    return orphans


def _check_collisions(root: Path, owners: dict[str, str]) -> None:
    """Across the combined destination set and the disk: no two paths that differ only by case, and no path
    that is both a file and a directory."""
    folded: dict[str, str] = {}
    for rel in sorted(owners):
        other = folded.setdefault(rel.casefold(), rel)
        if other != rel:
            raise BuildError(f"collision: {rel!r} and {other!r} differ only by case")
    dirs = {"/".join(rel.split("/")[:i]) for rel in owners for i in range(1, rel.count("/") + 1)}
    for rel in sorted(owners):
        if rel in dirs:
            raise BuildError(f"collision: {rel!r} would be both a file and a directory")
        path = root / rel
        if path.is_dir() and not path.is_symlink():
            raise BuildError(f"{rel!r} is a directory on disk; refusing to write a file there")
        parts = rel.split("/")
        for i in range(1, len(parts)):
            parent = root.joinpath(*parts[:i])
            if parent.exists() and not parent.is_dir():
                raise BuildError(f"{'/'.join(parts[:i])!r} is not a directory; cannot write {rel!r}")
        if path.parent.is_dir():
            for sibling in path.parent.iterdir():
                if sibling.name != parts[-1] and sibling.name.casefold() == parts[-1].casefold():
                    raise BuildError(f"collision: {rel!r} and existing {sibling.name!r} differ only by case")


def manifest_bytes(planned: dict[str, tuple[str, bytes]]) -> bytes:
    return "".join(f"{pid}\t{rel}\n" for rel, (pid, _) in sorted(planned.items())).encode("utf-8")


def write(root: Path, planned: dict[str, tuple[str, bytes]]) -> list[str]:
    """Validate every write and deletion first; only then touch the disk. Returns the changed paths."""
    root = Path(root)
    orphans = preflight(root, {rel: pid for rel, (pid, _) in planned.items()})
    changed = []
    for rel, (_, content) in sorted(planned.items()):
        path = root / rel
        if path.is_file() and path.read_bytes() == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        changed.append(rel)
    for rel in orphans:
        path = root / rel
        if path.is_file():
            path.unlink()
            changed.append(rel)
    manifest = manifest_bytes(planned)
    mpath = safepath.inside(root, MANIFEST)
    if not mpath.exists() or mpath.read_bytes() != manifest:
        mpath.write_bytes(manifest)
    return changed


def check_doc(root: Path, rel: str, owner: str) -> None:
    """Refuse unless `rel` is a documentation file (owner readme:<id>) that the manifest already assigns to `owner`."""
    root = Path(root)
    if not owner.startswith("readme:"):
        raise BuildError(f"{owner!r} is not a documentation owner; only readme:<id> files are refreshed alone")
    _check_destination(root, rel)
    if read_manifest(root).get(rel) != owner:
        raise BuildError(f"{rel!r} is not listed for {owner!r} in {MANIFEST}; run tools/build.py first")


def write_doc(root: Path, rel: str, owner: str, content: bytes) -> bool:
    """Documentation-only writer: rewrite one manifest-owned documentation file. Touches no other path and
    never the manifest. Returns True when the file changed."""
    check_doc(root, rel, owner)
    path = Path(root) / rel
    if path.is_file() and path.read_bytes() == content:
        return False
    path.write_bytes(content)
    return True
