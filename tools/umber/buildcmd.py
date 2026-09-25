"""The build, digest and mark commands."""
from __future__ import annotations

import dataclasses
from pathlib import Path

from . import docsgen, outputs, palette, portreadme, readme, registry, safepath
from .hygiene import scan_text


class CommandError(ValueError):
    pass


def _plan(root: Path):
    """(pal, ports, planned, intros). `planned` holds the port outputs; template-supplied port READMEs are
    split off into `intros` (port id -> text) because every port README is documentation, written with the
    per-port verification section after the port outputs exist."""
    pal = palette.load(safepath.inside(root, "palette/umber-calm.toml"))
    ports = registry.load_ports(safepath.inside(root, "ports.toml"))
    planned = outputs.plan(root, pal, ports)
    intros = portreadme.split_intros(planned, ports)
    planned.update(docsgen.plan(root, pal))
    return pal, ports, planned, intros


def _state(root: Path):
    pal, ports, planned, _ = _plan(root)
    return pal, ports, planned


def port_states(root: Path, ports, planned) -> dict[str, registry.TierInfo]:
    """Tier, current digest, covered files and full history for every port, from the files on disk."""
    by_port = outputs.paths_by_port(planned)
    records = registry.load_verifications(safepath.inside(root, "verifications.json"))
    visible = registry.publishable(root)
    states = {}
    for p in ports:
        paths = registry.digest_paths(root, p, by_port.get(p.id, []), visible)
        current = registry.digest(root, paths) if paths else "sha256:none"
        info = registry.tier(p, records.get(p.id, []), current)
        states[p.id] = dataclasses.replace(info, digest=current, inputs=tuple(paths),
                                           records=tuple(records.get(p.id, [])))
    return states


def _readme_text(text: str, pal, ports, states) -> str:
    new = readme.replace_section(text, "palette", readme.palette_table(pal))
    new = readme.replace_section(new, "ports", readme.ports_table(ports, states))
    return readme.replace_section(new, "verification", readme.verification_table(ports, states))


def _update_readme(root: Path, pal, ports, states) -> bool:
    path = safepath.inside(root, "README.md")
    text = path.read_text(encoding="utf-8")
    new = _readme_text(text, pal, ports, states)
    if new != text:
        path.write_bytes(new.encode("utf-8"))
        return True
    return False


def _check_readme(root: Path) -> None:
    """Raise ReadmeError before anything is written when a generated README section has no markers."""
    text = safepath.read_text(root, "README.md")
    for name in ("palette", "ports", "verification"):
        readme.replace_section(text, name, "")


def states(root: Path) -> dict[str, registry.TierInfo]:
    """Tier, digest, covered files and history of every port, from the files on disk. Writes nothing."""
    root = Path(root)
    _, ports, planned = _state(root)
    return port_states(root, ports, planned)


def stale(root: Path) -> list[str]:
    """Every generated path that is missing or differs from a fresh in-memory render: port outputs, generated docs,
    port READMEs, the main README sections, the manifest, and orphans (files a build would delete). Writes nothing.

    Documentation is rendered from the port files on disk, as the build does after writing them; when a port
    output is stale its README is compared against the old files, and the output itself is reported."""
    root = Path(root)
    pal, ports, planned, intros = _plan(root)
    found = outputs.stale(root, planned)
    states = port_states(root, ports, planned)
    docs = portreadme.plan_docs(ports, states, intros)
    found += outputs.stale(root, docs)
    text = safepath.read_text(root, "README.md")
    if _readme_text(text, pal, ports, states) != text:
        found.append("README.md")
    expected = {**planned, **docs}
    manifest = safepath.inside(root, outputs.MANIFEST)
    if not manifest.is_file() or manifest.read_bytes() != outputs.manifest_bytes(expected):
        found.append(outputs.MANIFEST)
    found += [rel for rel in outputs.read_manifest(root) if rel not in expected and (root / rel).exists()]
    return sorted(set(found))


def build(root: Path) -> list[str]:
    """Preflight the complete write and deletion set, then write the port outputs, then the documentation.

    The port READMEs show digests of the port files on disk, so they are rendered after the first write;
    every destination of both writes was validated before either of them touched the disk."""
    root = Path(root)
    pal, ports, planned, intros = _plan(root)
    docs = {portreadme.readme_rel(p): portreadme.owner(p) for p in ports}
    outputs.preflight(root, {**{rel: pid for rel, (pid, _) in planned.items()}, **docs})
    _check_readme(root)
    registry.load_verifications(safepath.inside(root, "verifications.json"))  # refuse a bad file before writing
    visible = registry.publishable(root)
    for p in ports:  # the digest sweep refuses symlinks and bad inputs: meet that before anything is written
        registry.digest_paths(root, p, [], visible, require_matches=False)
    previous = outputs.read_manifest(root)
    kept = {rel: (owner, (root / rel).read_bytes()) for rel, owner in docs.items()
            if rel in previous and (root / rel).is_file()}
    changed = outputs.write(root, {**planned, **kept})
    current = port_states(root, ports, planned)
    for rel in outputs.write(root, {**planned, **portreadme.plan_docs(ports, current, intros)}):
        if rel not in changed:
            changed.append(rel)
    if _update_readme(root, pal, ports, current):
        changed.append("README.md")
    return changed


def port_digest(root: Path, port_id: str) -> tuple[str, list[str]]:
    """(full current digest, covered files) for one port, computed from the files on disk. Writes nothing."""
    root = Path(root)
    _, ports, planned = _state(root)
    if port_id not in {p.id for p in ports}:
        raise CommandError(f"unknown port {port_id!r}")
    stale_paths = outputs.stale(root, planned)
    if stale_paths:
        raise CommandError(f"outputs are stale ({', '.join(stale_paths)}); run tools/build.py first")
    info = port_states(root, ports, planned)[port_id]
    return info.digest, list(info.inputs)


def mark(root: Path, port_id: str, status: str, *, digest: str, app_version: str, os_name: str,
         os_version: str, note: str, evidence: str, today: str) -> dict:
    """Record a verification of the exact tested bytes. Never builds (spec §6.5): afterwards it refreshes only
    documentation — this port's README and the main README sections — and never another file."""
    root = Path(root)
    if status not in registry.STATUSES:
        raise CommandError(f"status must be one of {registry.STATUSES}, got {status!r}")
    app_version = app_version.removeprefix("v")  # `v0.39.1` → `0.39.1`; validate_record then allows digits and dots only
    pal, ports, planned, intros = _plan(root)
    by_id = {p.id: p for p in ports}
    if port_id not in by_id:
        raise CommandError(f"unknown port {port_id!r}")
    port = by_id[port_id]
    own = {rel: v for rel, v in planned.items() if v[0] == port_id}
    if not own:
        raise CommandError(f"port {port_id!r} has no generated files to verify")
    stale_paths = outputs.stale(root, own)
    if stale_paths:
        raise CommandError(f"outputs are stale ({', '.join(stale_paths)}); run tools/build.py, then test again")
    states_before = port_states(root, ports, planned)
    current = states_before[port_id].digest
    if digest != current:
        raise CommandError(f"tested digest {digest} does not match the current files ({current}); test again")
    homepage = pal.meta["homepage"].rstrip("/") + "/"
    if evidence and not evidence.startswith(homepage):
        raise CommandError(f"evidence must be an issue, pull request or discussion of {homepage}")
    leaks = scan_text(note, "note")
    if leaks:
        raise CommandError("note contains personal data: " + "; ".join(leaks))
    record = {"status": status, "date": today, "app_version": app_version, "os": os_name,
              "os_version": os_version, "digest": current, "note": note, "evidence": evidence}
    try:
        registry.validate_record(port_id, record)
        outputs.check_doc(root, portreadme.readme_rel(port), portreadme.owner(port))
    except (registry.RegistryError, outputs.BuildError) as e:
        raise CommandError(str(e)) from None
    _check_readme(root)
    vpath = safepath.inside(root, "verifications.json")
    data = registry.load_verifications(vpath)
    data.setdefault(port_id, []).append(record)
    registry.save_verifications(vpath, data)
    after = port_states(root, ports, planned)
    outputs.write_doc(root, portreadme.readme_rel(port), portreadme.owner(port),
                      portreadme.render(port, after[port_id], intros.get(port_id)).encode("utf-8"))
    _update_readme(root, pal, ports, after)
    return record
