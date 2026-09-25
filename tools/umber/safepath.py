"""Containment for every repository file the tools read or write (spec §3 write safety).

A source or destination is refused when ANY component of its path (from the repository root down) is a symlink,
when it resolves outside the repository, and when it is or resolves inside `.git/`. So a link can neither copy outside
bytes into generated files and packages nor redirect a write, not even to another place inside the repository."""
from __future__ import annotations

from pathlib import Path


class UnsafePathError(ValueError):
    pass


def inside(root: Path, rel: str | Path) -> Path:
    """`root / rel` after checking it: not a symlink, and resolving inside the repository. The file need not exist."""
    root = Path(root)
    parts = Path(rel).parts
    shown = Path(rel).as_posix()
    if Path(rel).is_absolute() or ".." in parts:
        raise UnsafePathError(f"{shown} is not a relative path inside the repository")
    if any(part.casefold() == ".git" for part in parts):
        raise UnsafePathError(f"{shown} is inside .git; refusing to read or write there")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():  # lstat: the link itself, wherever it points
            link = current.relative_to(root).as_posix()
            raise UnsafePathError(f"{shown}: {link} is a symlink; refusing to read or write through it")
    path = root / rel
    real_root = root.resolve()
    resolved = path.resolve()
    if resolved != real_root and real_root not in resolved.parents:
        raise UnsafePathError(f"{shown} resolves outside the repository")
    git_dir = real_root / ".git"
    if resolved == git_dir or git_dir in resolved.parents:
        raise UnsafePathError(f"{shown} resolves inside .git; refusing to read or write there")
    return path


def read_bytes(root: Path, rel: str | Path) -> bytes:
    return inside(root, rel).read_bytes()


def read_text(root: Path, rel: str | Path) -> str:
    return read_bytes(root, rel).decode("utf-8")


def write_bytes(root: Path, rel: str | Path, data: bytes) -> None:
    inside(root, rel).write_bytes(data)
