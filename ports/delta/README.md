# delta — Umber Calm

Tier: 🧪 experimental

Target version: 0.18 · Format documentation: https://dandavison.github.io/delta/custom-themes.html

Verified on: —

## Install

Install the bat port first. Add `[include] path = /path/to/umber-calm.gitconfig` to ~/.gitconfig and set `[delta] features = umber-calm`.

## Uninstall

Remove the include and the features line.

## Verification checklist

- [ ] added/removed lines use the light 12% tint
- [ ] changed words use the 22% tint
- [ ] comments stay readable on both
- [ ] line numbers
- [ ] file and hunk headers

## Verification

Current digest: `sha256:3308e3be3a2464ab37da3d7366f8a999596e1f12eb764fad35459473328372ba`

Print it yourself with `python3 tools/build.py digest delta`. It covers these files:

- `ports/bat/Umber Calm.tmTheme`
- `ports/delta/umber-calm.gitconfig`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
