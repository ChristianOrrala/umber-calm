# sway — Umber Calm

Tier: 🧪 experimental

Target version: 1.10 · Format documentation: https://man.archlinux.org/man/sway.5.en

Verified on: —

## Install

Add `include /path/to/umber-calm.sway` to ~/.config/sway/config and run `swaymsg reload`.

## Uninstall

Remove the include and reload.

## Verification checklist

- [ ] focused window border uses the focus color
- [ ] unfocused and inactive windows
- [ ] urgent window

## Verification

Current digest: `sha256:6e205117113696d0ee51ee4d83f63580bbd6cb008bebae2ed235b64a6e9e0567`

Print it yourself with `python3 tools/build.py digest sway`. It covers these files:

- `ports/sway/umber-calm.sway`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
