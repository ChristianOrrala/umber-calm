# Starship — Umber Calm

Tier: ✅ supported

Target version: 1.20 · Format documentation: https://starship.rs/advanced-config/

Verified on: 1.27.0 · macOS 26.6.2 (2026-11-07)

## Install

Copy the [palettes.umber_calm] table into ~/.config/starship.toml and add `palette = "umber_calm"` at the top level. Use the palette names (text, muted, blue, …) in your module styles.

## Uninstall

Remove the palette line and the table.

## Verification checklist

- [ ] prompt segments render in palette colors
- [ ] error symbol uses red
- [ ] no raw hex in your styles is needed

## Verification

Current digest: `sha256:8dcecad55f8e92fcfd6a068f862fea808af61c42978297d39843ff0360afb8dc`

Print it yourself with `python3 tools/build.py digest starship`. It covers these files:

- `ports/starship/umber-calm.toml`

| Date | Result | App version | OS | OS version | Note | Evidence | Digest |
|---|---|---|---|---|---|---|---|
| 2026-11-07 | ✅ verified | 1.27.0 | macOS | 26.6.2 | Every palette name renders in its value, both new greys included; error prompt red. |  | `8dcecad55f8e` |
| 2026-09-28 | ✅ verified | 1.26.0 | macOS | 26.6.2 | Escape codes carry palette truecolor for every named style incl. the red error symbol; ANSI fallback without the palette line. |  | `5a93696bbb6f` |

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
