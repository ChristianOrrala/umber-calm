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

Current digest: `sha256:d955f89d442b9f6556830743a6a5a8fe9f47198a5f194c1d9cdd349ddc961641`

Print it yourself with `python3 tools/build.py digest termux`. It covers these files:

- `ports/termux/colors.properties`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
