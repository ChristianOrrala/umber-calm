# Waybar — Umber Calm

Tier: 🧪 experimental

Target version: 0.11 · Format documentation: https://github.com/Alexays/Waybar/wiki/Styling

Verified on: —

## Install

Copy umber-calm.css next to your style.css, add `@import "umber-calm.css";` at the top, and use the variables (@bg, @surface, @text, @muted, @focus, @red…) in your rules.

## Uninstall

Remove the import and the file.

## Verification checklist

- [ ] bar background
- [ ] module text
- [ ] focused workspace uses @focus
- [ ] warning/critical states

## Verification

Current digest: `sha256:52fb3b90c649cf46a2ffedaa3679aeddd0662d951a6741b313b38d5f462a67a7`

Print it yourself with `python3 tools/build.py digest waybar`. It covers these files:

- `ports/waybar/umber-calm.css`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
