# Windows Terminal — Umber Calm

Tier: 🧪 experimental

Target version: 1.21 · Format documentation: https://learn.microsoft.com/windows/terminal/customize-settings/color-schemes

Verified on: —

## Install

Open settings.json, add the object from umber-calm.json to the `schemes` array, and set `"colorScheme": "Umber Calm"` in a profile (or in profiles.defaults).

## Uninstall

Remove the colorScheme setting and the scheme object.

## Verification checklist

- [ ] background and text
- [ ] 16 ANSI colors
- [ ] selection
- [ ] cursor

## Verification

Current digest: `sha256:f21b0b6c213a263ba91dfb00363da955ed92cb8a198e3c8461c0ad75c193ccb6`

Print it yourself with `python3 tools/build.py digest windows-terminal`. It covers these files:

- `ports/windows-terminal/umber-calm.json`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
