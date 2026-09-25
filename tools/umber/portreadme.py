"""Per-port README.md generated from the registry and verification records (excluded from digests)."""
from __future__ import annotations

import re

from .readme import TIER_LABEL, cell, last_verified, verified_on
from .registry import Port, TierInfo

RESULT = {"verified": "✅ verified", "needs-fix": "⚠️ needs-fix"}
EVIDENCE = re.compile(r"/(?:issues|pull|discussions)/(\d+)$")


def readme_rel(port: Port) -> str:
    return f"ports/{port.id}/README.md"


def owner(port: Port) -> str:
    return f"readme:{port.id}"


def _evidence(url: str) -> str:
    m = EVIDENCE.search(url or "")
    return f"[#{m.group(1)}]({url})" if m else ""


def render(port: Port, info: TierInfo, intro: str | None = None) -> str:
    """The port README. `intro` is a template-supplied README (templates/<id>/README.md[.tmpl]): it replaces the
    generated title, and everything generated — tier, versions, install, checklist and the verification section
    with the digest, covered files and history — follows it."""
    lines = [intro.rstrip("\n") if intro is not None else f"# {port.name} — Umber Calm", ""]
    if port.archived_reason:
        lines += [f"> 📦 **Archived since {port.archived_since}:** {port.archived_reason} "
                  "The files stay downloadable but are no longer tested.", ""]
    if port.candidate_reason:
        lines += [f"> 🟡 **Candidate:** {port.candidate_reason}", ""]
    if port.risk:
        lines += [f"> ⚠️ **Warning:** {port.risk}", ""]
    stale = " (the last verification was for an earlier revision of these files)" if info.stale else ""
    record = last_verified(info)
    verified = f"{verified_on(info)} ({record['date']})" if record else "—"
    version = f"Target version: {port.target_version}"
    if port.min_version:
        version += f" · Minimum version: {port.min_version}"
    if port.docs != "internal":
        version += f" · Format documentation: {port.docs}"
    lines += [f"Tier: {TIER_LABEL[info.tier]}{stale}", "", version, "", f"Verified on: {verified}", "",
              "## Install", "", port.install, "",
              "## Uninstall", "", port.uninstall, "",
              "## Verification checklist", "", *[f"- [ ] {item}" for item in port.checklist], "",
              "## Verification", "",
              f"Current digest: `{info.digest}`", "",
              f"Print it yourself with `python3 tools/build.py digest {port.id}`. It covers these files:", "",
              *[f"- `{rel}`" for rel in info.inputs], ""]
    if info.records:
        lines += ["| Date | Result | App version | OS | OS version | Note | Evidence | Digest |",
                  "|---|---|---|---|---|---|---|---|"]
        for r in reversed(info.records):
            lines.append(f"| {r['date']} | {RESULT[r['status']]} | {cell(r['app_version'])} | {r['os']} | "
                         f"{cell(r['os_version'])} | {cell(r['note'])} | {_evidence(r['evidence'])} | `{r['digest'][7:19]}` |")
        lines.append("")
    else:
        lines += ["No verification recorded yet.", ""]
    lines += ["Generated from ports.toml and verifications.json — do not edit. "
              "MIT License — see the repository LICENSE.", ""]
    return "\n".join(lines)


def split_intros(planned: dict[str, tuple[str, bytes]], ports: list[Port]) -> dict[str, str]:
    """Remove template-supplied port READMEs from `planned` (they are documentation, never port outputs) and
    return them as {port id: text}; `render` uses each as the intro of that port's generated README."""
    intros = {}
    for port in ports:
        entry = planned.get(readme_rel(port))
        if entry is not None and entry[0] == port.id:
            intros[port.id] = planned.pop(readme_rel(port))[1].decode("utf-8")
    return intros


def plan_docs(ports: list[Port], states: dict[str, TierInfo], intros: dict[str, str]) -> dict[str, tuple[str, bytes]]:
    """Every port README, under the owner readme:<id>."""
    return {readme_rel(p): (owner(p), render(p, states[p.id], intros.get(p.id)).encode("utf-8")) for p in ports}
