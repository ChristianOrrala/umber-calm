"""Generated README sections."""
from __future__ import annotations

from . import color
from .palette import Palette
from .registry import CATEGORIES, Port, TierInfo

TIER_LABEL = {"supported": "✅ supported", "experimental": "🧪 experimental",
              "candidate": "🟡 candidate", "needs-fix": "⚠️ needs-fix"}
ARCHIVED_LABEL = "📦 archived"


class ReadmeError(ValueError):
    pass


def replace_section(text: str, name: str, body: str) -> str:
    begin, end = f"<!-- {name}:begin -->", f"<!-- {name}:end -->"
    i, j = text.find(begin), text.find(end)
    if i < 0 or j < 0 or j < i:
        raise ReadmeError(f"README is missing the {name!r} markers")
    return text[: i + len(begin)] + "\n" + body + "\n" + text[j:]


def palette_table(pal: Palette) -> str:
    bg = pal.colors["bg"]
    rows = ["| Name | Hex | Contrast on `bg` |", "|---|---|---|"]
    for name, hx in pal.colors.items():
        ratio = "—" if name == "bg" else f"{color.contrast(hx, bg):.1f}:1"
        rows.append(f"| `{name}` | `{hx}` | {ratio} |")
    return "\n".join(rows)


def cell(text: str) -> str:
    """Text safe inside one Markdown table cell: `|` escaped, line breaks turned into spaces."""
    return " ".join(str(text).replace("|", "\\|").splitlines())


def _version(p: Port) -> str:
    return f"{p.target_version} (min {p.min_version})" if p.min_version else p.target_version


def download(p: Port) -> str:
    """Link to the port's files; a port whose files live at the repository root links to its README."""
    if p.output_root == ".":
        return f"[ports/{p.id}/](ports/{p.id}/README.md)"
    return f"[{p.output_root}/]({p.output_root}/)"


def last_verified(info: TierInfo) -> dict | None:
    """The newest `verified` record, from the recorded history only."""
    records = list(info.records) or ([info.last] if info.last else [])
    return next((r for r in reversed(records) if r["status"] == "verified"), None)


def verified_on(info: TierInfo) -> str:
    record = last_verified(info)
    if record is None:
        return "—"
    where = " ".join(x for x in (record["os"], record["os_version"]) if x)
    return f"{record['app_version']} · {where}"


def notes(p: Port, info: TierInfo) -> str:
    parts = []
    if p.candidate_reason:
        parts.append(f"🟡 {p.candidate_reason}")
    if info.tier == "needs-fix" and info.last and info.last.get("note"):
        parts.append(f"⚠️ needs-fix: {info.last['note']}")
    if p.risk:
        parts.append(f"⚠️ {p.risk}")
    return cell(" · ".join(parts))


def ports_table(ports: list[Port], tiers: dict[str, TierInfo]) -> str:
    rows = ["| App | Category | Tier | Download | Target version | Verified on | Notes |", "|---|---|---|---|---|---|---|"]
    for category in CATEGORIES:
        for p in sorted((p for p in ports if p.category == category and not p.archived_reason),
                        key=lambda p: p.name.lower()):
            info = tiers[p.id]
            rows.append(f"| {cell(p.name)} | {category} | {TIER_LABEL[info.tier]} | {download(p)} | "
                        f"{cell(_version(p))} | {cell(verified_on(info))} | {notes(p, info)} |")
    archived = sorted((p for p in ports if p.archived_reason), key=lambda p: p.name.lower())
    if archived:
        rows += ["", "**Archived** — still downloadable, no longer maintained:", "",
                 "| App | Since | Reason | Download |", "|---|---|---|---|"]
        rows += [f"| {cell(p.name)} | {p.archived_since} | {ARCHIVED_LABEL} — {cell(p.archived_reason)} | "
                 f"{download(p)} |" for p in archived]
    return "\n".join(rows)


def verification_table(ports: list[Port], tiers: dict[str, TierInfo]) -> str:
    rows = ["| App | Tier | Last verified | App version | OS | Digest | Evidence |",
            "|---|---|---|---|---|---|---|"]
    for p in sorted(ports, key=lambda p: p.name.lower()):
        info = tiers[p.id]
        last = info.last or {}
        date = last.get("date", "—")
        if info.stale:
            date = f"{date} (earlier revision)"
        os_name = " ".join(x for x in (last.get("os", ""), last.get("os_version", "")) if x)
        short = f"`{info.digest[7:19]}`" if info.digest else ""
        evidence = f"[link]({last['evidence']})" if last.get("evidence") else ""
        label = f"{ARCHIVED_LABEL}" if p.archived_reason else TIER_LABEL[info.tier]
        rows.append(f"| {cell(p.name)} | {label} | {cell(date)} | {cell(last.get('app_version', ''))} | {cell(os_name)} | "
                    f"{short} | {evidence} |")
    return "\n".join(rows)
