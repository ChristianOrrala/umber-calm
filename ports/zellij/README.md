# Zellij — Umber Calm

Tier: 🧪 experimental

Target version: 0.45.1 · Format documentation: https://zellij.dev/documentation/themes.html

Verified on: —

## Install

Uses Zellij's component theme format (written for Zellij 0.45.1; older releases that only read the legacy 11-color palette are not supported). Copy umber-calm.kdl to ~/.config/zellij/themes/ and set `theme "umber-calm"` in config.kdl.

## Uninstall

Remove the theme line and the file.

## Verification checklist

- [ ] status bar and tab bar: active tab and current mode are orange (focus), inactive ones neutral
- [ ] focused pane frame is orange; other pane frames are muted
- [ ] focused frame stays orange in other modes (resize, scroll, locked)
- [ ] session manager and plugin lists/tables readable
- [ ] search highlights

## Verification

Current digest: `sha256:8ad27fb2e46e87fc18c5d70fa7ad80559b87c9ab2889408eb1637cb7b6b1c16b`

Print it yourself with `python3 tools/build.py digest zellij`. It covers these files:

- `ports/zellij/umber-calm.kdl`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
