# JSON palette

`umber-calm.json` exports the Umber Calm palette (version 0.1.0, release 0.5.0, schema 1) for tooling: metadata, colors, the 16 ANSI slots, the role contracts (syntax, ui, diag, term) resolved to hex, and tint amounts.

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

Current digest: `sha256:1a2d7d3a01e164f82b328ef8b11b2312e9d72116c0cc0ed770fb93371802fa89`

Print it yourself with `python3 tools/build.py digest json`. It covers these files:

- `ports/json/umber-calm.json`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
