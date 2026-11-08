# Termux — Umber Calm

Tier: 🧪 experimental

Target version: 0.118 · Format documentation: https://github.com/termux/termux-app

Verified on: —

## Install

Copy colors.properties to ~/.termux/colors.properties and run `termux-reload-settings`.

## Uninstall

Delete ~/.termux/colors.properties and run `termux-reload-settings`.

## Verification checklist

- [ ] background and text
- [ ] 16 ANSI colors
- [ ] cursor

## Verification

Current digest: `sha256:ebe456bde2fca864d19a715c547e0c2cc0824abe0381784385d7c0c118713f3f`

Print it yourself with `python3 tools/build.py digest termux`. It covers these files:

- `ports/termux/colors.properties`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
