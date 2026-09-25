"""Release gate (spec §14): everything a tag must satisfy before its artifacts are published."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from . import buildcmd, package, palette, registry

LAUNCH_PORTS = ("neovim", "vscode", "wezterm", "tmux", "starship", "zellij", "claude-code")


def gate(root: Path, tag: str, *, launch: tuple[str, ...] = LAUNCH_PORTS) -> list[str]:
    root = Path(root)
    problems: list[str] = []
    git = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True)
    if git.returncode != 0:
        problems.append(f"git status failed: {git.stderr.strip()}")
    elif git.stdout.strip():
        problems.append("working tree is not clean: commit or remove every change before tagging")
    release = palette.load(root / "palette" / "umber-calm.toml").meta["release"]
    if tag != f"v{release}":
        problems.append(f"tag {tag!r} does not match meta.release {release!r} (expected 'v{release}')")
    try:
        stale = buildcmd.stale(root)
    except ValueError as e:  # every build error (unsafe path, bad manifest, template, registry) is a ValueError
        problems.append(f"cannot render the generated files: {e}")
        return problems
    if stale:
        more = f" and {len(stale) - 10} more" if len(stale) > 10 else ""
        problems.append(f"generated files are stale (run tools/build.py): {', '.join(stale[:10])}{more}")
        return problems
    ports = {p.id: p for p in registry.load_ports(root / "ports.toml")}
    states = buildcmd.states(root)
    for pid in launch:
        if pid not in ports:
            problems.append(f"launch port {pid!r} is not in ports.toml")
        elif not ports[pid].archived_reason and states[pid].tier != "supported":
            problems.append(f"launch port {pid!r} is {states[pid].tier}; it must be supported with its current digest")
    committed = root / "dist" / package.SUMS
    with tempfile.TemporaryDirectory() as tmp:
        try:
            package.package(root, Path(tmp) / "dist")
        except package.PackageError as e:
            problems.append(f"packaging failed: {e}")
        else:
            rebuilt = (Path(tmp) / "dist" / package.SUMS).read_bytes()
            if not committed.is_file():
                problems.append("dist/SHA256SUMS is not committed (run tools/package.py, then commit it)")
            elif committed.read_bytes() != rebuilt:
                problems.append("rebuilt artifacts differ from dist/SHA256SUMS (run tools/package.py, then commit)")
    return problems
