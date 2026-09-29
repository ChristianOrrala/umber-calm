"""Generated README sections."""
from __future__ import annotations

from . import color
from .palette import CONTRACTS, Palette
from .registry import CATEGORIES, Port, TierInfo

TIER_LABEL = {"supported": "✅ supported", "experimental": "🧪 experimental",
              "candidate": "🟡 candidate", "needs-fix": "⚠️ needs-fix"}
TIER_ORDER = ("supported", "experimental", "candidate", "needs-fix")
TIER_MEANING = {"supported": "tested in the real app, on the exact files",
                "experimental": "format confirmed, not yet tested in the app",
                "candidate": "format not confirmed",
                "needs-fix": "a real-app test found a problem"}
ARCHIVED_LABEL = "📦 archived"

# How each role reads in the README's "Used for" column; None leaves a role out (it repeats another label).
ROLE_LABELS = {
    ("syntax", "keyword"): "keywords", ("syntax", "preproc"): "preprocessor", ("syntax", "function"): "functions",
    ("syntax", "tag"): "tags", ("syntax", "type"): "types", ("syntax", "namespace"): "namespaces",
    ("syntax", "attribute"): "attributes", ("syntax", "string"): "strings", ("syntax", "escape"): "escapes",
    ("syntax", "constant"): "constants", ("syntax", "builtin"): "built-ins", ("syntax", "variable"): "variables",
    ("syntax", "operator"): "operators", ("syntax", "comment"): "comments", ("syntax", "heading"): "headings",
    ("syntax", "link"): "links", ("syntax", "code"): "inline code",
    ("ui", "bg"): "background", ("ui", "surface"): "panels", ("ui", "chrome"): "chrome",
    ("ui", "selection_bg"): "selection", ("ui", "selection_fg"): None, ("ui", "border_strong"): "strong borders",
    ("ui", "border"): "borders", ("ui", "text"): "body text", ("ui", "text_secondary"): "secondary text",
    ("ui", "line_number"): "line numbers", ("ui", "line_number_active"): "current line number",
    ("ui", "text_dim"): "dim text", ("ui", "focus"): "focus",
    ("diag", "error"): "errors", ("diag", "warning"): "warnings", ("diag", "info"): "info", ("diag", "hint"): "hints",
    ("diag", "ok"): "success", ("diag", "diff_add"): "added lines", ("diag", "diff_delete"): "deleted lines",
    ("diag", "diff_change"): "changed lines", ("diag", "search"): "search",
    ("term", "background"): None, ("term", "foreground"): None, ("term", "cursor"): "cursor",
    ("term", "cursor_text"): None, ("term", "selection_bg"): None, ("term", "selection_fg"): None,
}


class ReadmeError(ValueError):
    pass


def replace_section(text: str, name: str, body: str) -> str:
    begin, end = f"<!-- {name}:begin -->", f"<!-- {name}:end -->"
    i, j = text.find(begin), text.find(end)
    if i < 0 or j < 0 or j < i:
        raise ReadmeError(f"README is missing the {name!r} markers")
    return text[: i + len(begin)] + "\n" + body + "\n" + text[j:]


def used_for(pal: Palette, name: str) -> str:
    """What a color is used for, read from the role map (falling back to the ANSI slots it fills)."""
    labels: list[str] = []
    for contract in CONTRACTS:
        for role, target in pal.roles[contract].items():
            if (contract, role) not in ROLE_LABELS:
                raise ReadmeError(f"[roles.{contract}] {role} has no README label: add it to readme.ROLE_LABELS "
                                  f"(or map it to None to leave it out of the palette table)")
            label = ROLE_LABELS[(contract, role)]
            if target == name and label and label not in labels:
                labels.append(label)
    if not labels:
        slots = [slot for slot, hx in pal.ansi.items() if hx == pal.colors[name]]
        labels = ["ANSI " + slot.replace("_", " ") for slot in slots]
    text = ", ".join(labels)
    return text[:1].upper() + text[1:] if text else "—"


def palette_table(pal: Palette) -> str:
    bg = pal.colors["bg"]
    rows = ["|  | Name | Hex | Contrast on `bg` | Used for |", "|---|---|---|---|---|"]
    for name, hx in pal.colors.items():
        ratio = "—" if name == "bg" else f"{color.contrast(hx, bg):.1f}:1"
        img = f'<img src="docs/swatches/{name}.svg" width="20" height="20" alt="{name} {hx}">'
        rows.append(f"| {img} | `{name}` | `{hx}` | {ratio} | {cell(used_for(pal, name))} |")
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


def _details(summary: str, table: list[str], open_: bool = False) -> list[str]:
    """A collapsible block; the blank line after <summary> lets GitHub render the Markdown table inside it."""
    return ["<details open>" if open_ else "<details>", f"<summary>{summary}</summary>", "", *table, "", "</details>"]


def ports_table(ports: list[Port], tiers: dict[str, TierInfo]) -> str:
    """Ports grouped by tier: supported open, every other tier collapsed; empty tiers are left out."""
    live = [p for p in ports if not p.archived_reason]
    order = {c: i for i, c in enumerate(CATEGORIES)}
    blocks: list[str] = []
    for tier in TIER_ORDER:
        group = sorted((p for p in live if tiers[p.id].tier == tier), key=lambda p: (order[p.category], p.name.lower()))
        if not group:
            continue
        table = ["| App | Category | Download | Target version | Verified on | Notes |", "|---|---|---|---|---|---|"]
        for p in group:
            info = tiers[p.id]
            table.append(f"| {cell(p.name)} | {p.category} | {download(p)} | {cell(_version(p))} | "
                         f"{cell(verified_on(info))} | {notes(p, info)} |")
        summary = f"<b>{TIER_LABEL[tier]} ({len(group)})</b>: {TIER_MEANING[tier]}"
        blocks += [*_details(summary, table, open_=tier == "supported"), ""]
    archived = sorted((p for p in ports if p.archived_reason), key=lambda p: p.name.lower())
    if archived:
        table = ["| App | Since | Reason | Download |", "|---|---|---|---|"]
        table += [f"| {cell(p.name)} | {p.archived_since} | {ARCHIVED_LABEL} — {cell(p.archived_reason)} | "
                  f"{download(p)} |" for p in archived]
        summary = f"<b>{ARCHIVED_LABEL} ({len(archived)})</b>: still downloadable, no longer maintained"
        blocks += [*_details(summary, table), ""]
    return "\n".join(blocks).rstrip("\n")


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
