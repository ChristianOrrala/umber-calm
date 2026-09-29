# herdr — Umber Calm

> ⚠️ **Warning:** herdr has one red token: it marks blocked agents and needs-attention notices as well as delete confirmations.

Tier: ✅ supported

Target version: 0.9.1 · Format documentation: https://herdr.dev/docs/configuration/

Verified on: 0.9.1 · macOS 26.6.2 (2026-09-29)

## Install

herdr has no includes: paste the contents of umber-calm.toml into ~/.config/herdr/config.toml, replacing any [theme] and [theme.custom] tables, then run `herdr server reload-config`.

## Uninstall

Remove the pasted [theme] and [theme.custom] tables and reload the config.

## Verification checklist

- [ ] panes on bg, sidebar a step lighter
- [ ] focused pane border and active popup are orange (focus); nothing else is
- [ ] active space and agent row readable, navigate cursor row distinct from it
- [ ] agent states: working yellow, done green, blocked red, unseen blue or cyan
- [ ] secondary labels (workspace numbers, headers, inactive tabs) readable
- [ ] worktree and settings overlays readable

## Verification

Current digest: `sha256:b10fed21b5e9730fda3037d0210abe411e7ea05bcac08efb511f6618baee3bdc`

Print it yourself with `python3 tools/build.py digest herdr`. It covers these files:

- `ports/herdr/umber-calm.toml`

| Date | Result | App version | OS | OS version | Note | Evidence | Digest |
|---|---|---|---|---|---|---|---|
| 2026-09-29 | ✅ verified | 0.9.1 | macOS | 26.6.2 |  |  | `b10fed21b5e9` |

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
