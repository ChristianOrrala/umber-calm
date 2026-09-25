# Alacritty — Umber Calm

Tier: 🧪 experimental

Target version: 0.14 · Format documentation: https://alacritty.org/config-alacritty.html

Verified on: —

## Install

Copy umber-calm.toml to ~/.config/alacritty/themes/ and add `import = ["~/.config/alacritty/themes/umber-calm.toml"]` under [general] in alacritty.toml.

## Uninstall

Remove the import and the file.

## Verification checklist

- [ ] background and text
- [ ] 16 ANSI colors
- [ ] selection
- [ ] cursor
- [ ] search matches
- [ ] vi-mode cursor

## Verification

Current digest: `sha256:a80cd10efbe69a0a4bcfa9a942d4599a6c191e58e8615df3091007ba87a7d9f0`

Print it yourself with `python3 tools/build.py digest alacritty`. It covers these files:

- `ports/alacritty/umber-calm.toml`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
