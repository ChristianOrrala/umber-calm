# tmux — Umber Calm

Tier: 🧪 experimental

Target version: 3.4 · Format documentation: https://github.com/tmux/tmux/wiki

Verified on: —

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

Current digest: `sha256:58c29007c9b7b223509dbaa4d94c04f7cf7a6153fd82d429e0e6328b53d76358`

Print it yourself with `python3 tools/build.py digest tmux`. It covers these files:

- `ports/tmux/umber-calm.tmux`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
