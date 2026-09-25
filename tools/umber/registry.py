"""Port registry (ports.toml), verification records (verifications.json), digests, tiers."""
from __future__ import annotations

import datetime
import hashlib
import json
import re
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from . import safepath

CATEGORIES = ("terminal", "multiplexer", "shell", "cli", "editor", "desktop",
              "app", "web", "ai", "scheme", "data")
REQUIRED = ("id", "name", "category", "phase", "output_root", "docs", "format_confirmed",
            "target_version", "install", "uninstall", "checklist")
OPTIONAL = ("risk", "min_version", "inputs", "syntax_check", "syntax_exempt", "archived", "candidate_reason")
SYNTAX_FORMATS = ("vscode", "sublime", "zed", "helix", "tmtheme", "vim",
                  "jetbrains", "fish", "obsidian", "opencode")  # Part 3 extends this tuple (Tasks 22–26)
ID_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
SEMVER_RE = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
STATUSES = ("verified", "needs-fix")
OS_NAMES = ("macOS", "Windows", "Linux", "Android", "iOS", "web")
RECORD_KEYS = ("status", "date", "app_version", "os", "os_version", "digest", "note", "evidence")
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
OS_VERSION_RE = re.compile(r"([0-9]+(\.[0-9]+)*)?")
APP_VERSION_RE = re.compile(r"[0-9]+(\.[0-9]+)*")
APP_VERSION_MAX = 40
EVIDENCE_RE = re.compile(r"https://github\.com/ChristianOrrala/umber-calm/(issues|pull|discussions)/\d+")
NOTE_MAX = 200
SWEEP_SKIP = {".DS_Store", "__pycache__", ".git"}  # never covered when the repository is not a git work tree


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Port:
    id: str
    name: str
    category: str
    phase: int
    output_root: str
    docs: str
    format_confirmed: bool
    target_version: str
    install: str
    uninstall: str
    checklist: tuple[str, ...]
    risk: str = ""
    min_version: str = ""
    inputs: tuple[str, ...] = ()
    syntax_check: dict | None = None       # {"file": str, "format": one of SYNTAX_FORMATS}
    syntax_exempt: str = ""                # reason, when syntax.* refs are exported as data or checked elsewhere
    archived_reason: str = ""
    archived_since: str = ""
    candidate_reason: str = ""             # what is unconfirmed; required exactly when format_confirmed is false


def _safe_relative(value: str) -> bool:
    path = PurePosixPath(value)
    return (bool(value) and "\\" not in value and not path.is_absolute()
            and ".." not in path.parts and not re.match(r"[A-Za-z]:", value))


def _port(entry: dict) -> Port:
    pid = entry.get("id", "?")
    for key in REQUIRED:
        if key not in entry:
            raise RegistryError(f"port {pid!r}: missing field {key!r}")
    unknown = set(entry) - set(REQUIRED) - set(OPTIONAL)
    if unknown:
        raise RegistryError(f"port {pid!r}: unknown fields {sorted(unknown)}")
    if not ID_RE.fullmatch(pid):
        raise RegistryError(f"port {pid!r}: id must match {ID_RE.pattern}")
    if entry["category"] not in CATEGORIES:
        raise RegistryError(f"port {pid!r}: category {entry['category']!r} is not one of {CATEGORIES}")
    if not isinstance(entry["format_confirmed"], bool):
        raise RegistryError(f"port {pid!r}: format_confirmed must be true or false")
    if not isinstance(entry["phase"], int) or isinstance(entry["phase"], bool):
        raise RegistryError(f"port {pid!r}: phase must be an integer")
    if entry["output_root"] != "." and not _safe_relative(entry["output_root"]):
        raise RegistryError(f"port {pid!r}: output_root must be a relative POSIX path")
    checklist = entry["checklist"]
    if not isinstance(checklist, list) or not checklist or not all(isinstance(c, str) for c in checklist):
        raise RegistryError(f"port {pid!r}: checklist must be a non-empty list of strings")
    inputs = entry.get("inputs", [])
    if not isinstance(inputs, list) or not all(isinstance(g, str) and _safe_relative(g) for g in inputs):
        raise RegistryError(f"port {pid!r}: inputs must be a list of relative POSIX glob patterns")
    sc = entry.get("syntax_check")
    if sc is not None:
        if (not isinstance(sc, dict) or set(sc) != {"file", "format"} or sc["format"] not in SYNTAX_FORMATS
                or not isinstance(sc["file"], str) or not _safe_relative(sc["file"])):
            raise RegistryError(f"port {pid!r}: syntax_check must be {{ file = <relative path>, format = one of {SYNTAX_FORMATS} }}")
    exempt = entry.get("syntax_exempt", "")
    if not isinstance(exempt, str) or (sc is not None and exempt):
        raise RegistryError(f"port {pid!r}: syntax_exempt is a reason string and excludes syntax_check")
    reason_c = entry.get("candidate_reason", "")
    if entry["format_confirmed"] and "candidate_reason" in entry:
        raise RegistryError(f"port {pid!r}: candidate_reason is only for candidates (format_confirmed = false)")
    if not entry["format_confirmed"] and (not isinstance(reason_c, str) or not reason_c.strip()):
        raise RegistryError(f"port {pid!r}: a candidate (format_confirmed = false) needs candidate_reason, "
                            "saying what is unconfirmed")
    archived = entry.get("archived")
    reason = since = ""
    if archived is not None:
        if (not isinstance(archived, dict) or set(archived) != {"reason", "since"}
                or not str(archived["reason"]).strip() or not SEMVER_RE.fullmatch(str(archived["since"]))):
            raise RegistryError(f"port {pid!r}: archived must be {{ reason = <text>, since = <X.Y.Z> }}")
        reason, since = archived["reason"], archived["since"]
    fields = {k: entry[k] for k in REQUIRED}
    return Port(**{**fields, "checklist": tuple(checklist)}, risk=entry.get("risk", ""),
                min_version=entry.get("min_version", ""), inputs=tuple(inputs), syntax_check=sc,
                syntax_exempt=exempt, archived_reason=reason, archived_since=since, candidate_reason=reason_c)


def load_ports(path: Path) -> list[Port]:
    try:
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise RegistryError(f"{path}: {e}") from None
    ports, seen = [], set()
    for entry in data.get("port", []):
        port = _port(entry)
        if port.id in seen:
            raise RegistryError(f"duplicate port id {port.id!r}")
        seen.add(port.id)
        ports.append(port)
    return ports


def validate_record(pid: str, record: dict) -> None:
    where = f"verifications.json: {pid!r}"
    if not isinstance(record, dict) or tuple(sorted(record)) != tuple(sorted(RECORD_KEYS)):
        raise RegistryError(f"{where}: a record has exactly the keys {RECORD_KEYS}")
    if not all(isinstance(record[k], str) for k in RECORD_KEYS):
        raise RegistryError(f"{where}: every record value is a string")
    if record["status"] not in STATUSES:
        raise RegistryError(f"{where}: status must be one of {STATUSES}")
    try:
        if not DATE_RE.fullmatch(record["date"]):
            raise ValueError
        datetime.date.fromisoformat(record["date"])  # a real calendar date
    except ValueError:
        raise RegistryError(f"{where}: date must be a real date written YYYY-MM-DD") from None
    if not APP_VERSION_RE.fullmatch(record["app_version"]) or len(record["app_version"]) > APP_VERSION_MAX:
        raise RegistryError(f"{where}: app_version must be digits and dots (at most {APP_VERSION_MAX} characters)")
    if record["os"] not in OS_NAMES:
        raise RegistryError(f"{where}: os must be one of {OS_NAMES}")
    if not OS_VERSION_RE.fullmatch(record["os_version"]):
        raise RegistryError(f"{where}: os_version must be digits and dots, or empty")
    if not DIGEST_RE.fullmatch(record["digest"]):
        raise RegistryError(f"{where}: digest must be the full sha256:<64 hex>")
    note = record["note"]
    if len(note) > NOTE_MAX or "\n" in note or "\r" in note:
        raise RegistryError(f"{where}: note must be one line of at most {NOTE_MAX} characters")
    if record["evidence"] and not EVIDENCE_RE.fullmatch(record["evidence"]):
        raise RegistryError(f"{where}: evidence must be empty or a GitHub issue, pull request or discussion URL")


def _not_a_link(path: Path) -> Path:
    path = Path(path)
    if path.is_symlink():
        raise safepath.UnsafePathError(f"{path.name} is a symlink; refusing to read or write through it")
    return path


def load_verifications(path: Path) -> dict[str, list[dict]]:
    path = _not_a_link(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RegistryError(f"{path.name}: {e}") from None
    if not isinstance(data, dict):
        raise RegistryError(f"{path.name}: expected an object of port id -> list of records")
    for pid, records in data.items():
        if not isinstance(records, list):
            raise RegistryError(f"{path.name}: {pid!r} must map to a list of records")
        for record in records:
            validate_record(pid, record)
    return data


def save_verifications(path: Path, data: dict) -> None:
    for pid, records in data.items():
        for record in records:
            validate_record(pid, record)
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    _not_a_link(path).write_bytes(text.encode("utf-8"))


def publishable(root: Path) -> set[str] | None:
    """Files git would publish: tracked plus untracked-but-not-ignored. None when `root` is not a git work tree."""
    root = Path(root)
    if not (root / ".git").exists():
        return None
    result = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                            cwd=root, capture_output=True)
    if result.returncode != 0:
        raise RegistryError(f"git ls-files failed: {result.stderr.decode('utf-8', 'replace').strip()}")
    return {n for n in result.stdout.decode("utf-8").split("\0") if n}


def _covered(root: Path, candidates, visible: set[str] | None) -> list[str]:
    """Regular files among `candidates` that would be published; a symlink is refused, never followed."""
    found = []
    for p in candidates:
        rel = p.relative_to(root).as_posix()
        parts = rel.split("/")
        if ".git" in parts or (visible is None and SWEEP_SKIP & set(parts)):
            continue
        if visible is not None and rel not in visible and not p.is_dir():
            continue
        safepath.inside(root, rel)
        if p.is_file():
            found.append(rel)
    return found


def digest_paths(root: Path, port: Port, generated: list[str], visible: set[str] | None = None, *,
                 require_matches: bool = True) -> list[str]:
    """Every file whose bytes the port's verification certifies (spec §7.3): its generated files, its `inputs`
    and every file under its port directory — only files git would publish (tracked or untracked-but-not-ignored;
    outside git, everything but OS and cache files). `visible` is `publishable(root)`, computed when omitted.
    `require_matches=False` only validates the sources (the build does that before writing, when an input may be a
    file the same build is about to generate)."""
    root = Path(root)
    if visible is None:
        visible = publishable(root)
    paths = set(generated)
    for pattern in port.inputs:
        matched = _covered(root, sorted(root.glob(pattern)), visible)
        if not matched and require_matches:
            raise RegistryError(f"port {port.id!r}: inputs glob {pattern!r} matches no file")
        paths.update(matched)
    if port.output_root != ".":
        safepath.inside(root, port.output_root)
        base = root / port.output_root
        if base.is_dir():
            paths.update(_covered(root, sorted(base.rglob("*")), visible))
    readme = (PurePosixPath(port.output_root) / "README.md").as_posix()
    paths.discard(readme)
    return sorted(paths)


def digest(root: Path, rel_paths: list[str]) -> str:
    h = hashlib.sha256()
    for rel in sorted(rel_paths):
        h.update(rel.encode("utf-8") + b"\0")
        h.update(safepath.read_bytes(root, rel) + b"\0")
    return "sha256:" + h.hexdigest()


@dataclass(frozen=True)
class TierInfo:
    tier: str
    last: dict | None
    stale: bool
    digest: str = ""
    inputs: tuple[str, ...] = ()
    records: tuple[dict, ...] = field(default=())


def tier(port: Port, records: list[dict], current_digest: str) -> TierInfo:
    last = records[-1] if records else None
    if last and last["status"] == "needs-fix":
        return TierInfo("needs-fix", last, False)
    if last and last["status"] == "verified" and last["digest"] == current_digest:
        return TierInfo("supported", last, False)
    base = "experimental" if port.format_confirmed else "candidate"
    return TierInfo(base, last, bool(last and last["status"] == "verified"))
