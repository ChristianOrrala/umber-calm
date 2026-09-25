# Claude Code — Umber Calm

Tier: 🧪 experimental

Target version: 2.1.282 · Format documentation: https://code.claude.com/docs/en/terminal-config

Verified on: —

## Install

Copy umber-calm.json to ~/.claude/themes/ and select it with /theme (custom:umber-calm). It builds on the dark-ansi base, so use it together with an Umber Calm terminal port.

## Uninstall

Pick another theme with /theme and delete the file.

## Verification checklist

- [ ] message backgrounds
- [ ] composerSidebarBackground visibly applied: the diff side panel is the surface color, not gray
- [ ] diff +/− counts readable (green/red)
- [ ] no gray bands on added rows

## Verification

Current digest: `sha256:69ea78169c346b9c0ea58b79358954cd50001cf6464026348d39193ad9e31263`

Print it yourself with `python3 tools/build.py digest claude-code`. It covers these files:

- `ports/claude-code/umber-calm.json`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
