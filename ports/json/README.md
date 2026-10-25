# JSON palette

`umber-calm.json` exports the Umber Calm palette (version 0.1.0, release 0.2.1, schema 1) for tooling: metadata, colors, the 16 ANSI slots, the role contracts (syntax, ui, diag, term) resolved to hex, and tint amounts.

Tier: 🧪 experimental

Target version: schema 1

Verified on: —

## Install

Read ports/json/umber-calm.json from your tooling.

## Uninstall

Stop reading the file.

## Verification checklist

- [ ] parses as JSON
- [ ] contains every metadata key, color, ANSI slot, role and tint

## Verification

Current digest: `sha256:5154d75476eccd29d415c0dc1d1f99a705b1a797dfd8e33cc4d456e99b4ef7c3`

Print it yourself with `python3 tools/build.py digest json`. It covers these files:

- `ports/json/umber-calm.json`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
