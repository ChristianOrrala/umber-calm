# Starship — Umber Calm

Tier: 🧪 experimental

Target version: 1.20 · Format documentation: https://starship.rs/advanced-config/

Verified on: —

## Install

Copy the [palettes.umber_calm] table into ~/.config/starship.toml and add `palette = "umber_calm"` at the top level. Use the palette names (text, muted, blue, …) in your module styles.

## Uninstall

Remove the palette line and the table.

## Verification checklist

- [ ] prompt segments render in palette colors
- [ ] error symbol uses red
- [ ] no raw hex in your styles is needed

## Verification

Current digest: `sha256:5a93696bbb6f860202bbc7433b36e465054bf0e50f6fc7837a9b8174511f497a`

Print it yourself with `python3 tools/build.py digest starship`. It covers these files:

- `ports/starship/umber-calm.toml`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
