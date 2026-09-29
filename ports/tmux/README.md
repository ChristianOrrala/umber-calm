# tmux — Umber Calm

Tier: ✅ supported

Target version: 3.4 · Format documentation: https://github.com/tmux/tmux/wiki

Verified on: 3.7 · macOS 26.6.2 (2026-09-28)

## Install

Copy umber-calm.tmux to ~/.config/tmux/ and add `source-file ~/.config/tmux/umber-calm.tmux` to tmux.conf, then `tmux source-file ~/.config/tmux/tmux.conf`.

## Uninstall

Remove the source-file line and the file.

## Verification checklist

- [ ] status bar
- [ ] current window amber
- [ ] pane borders (active amber)
- [ ] copy-mode selection and search matches
- [ ] messages

## Verification

Current digest: `sha256:dfae7360e1c4899e140bf05f9d827646fefcc73f54f0b273a86dfc1811d234c3`

Print it yourself with `python3 tools/build.py digest tmux`. It covers these files:

- `ports/tmux/umber-calm.tmux`

| Date | Result | App version | OS | OS version | Note | Evidence | Digest |
|---|---|---|---|---|---|---|---|
| 2026-09-28 | ✅ verified | 3.7 | macOS | 26.6.2 | tmux 3.7c. Status, current/activity windows, pane borders, message, copy-mode selection and search pixel-checked after the lowercase-hex fix. |  | `dfae7360e1c4` |

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
