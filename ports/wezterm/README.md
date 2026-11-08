# WezTerm — Umber Calm

Tier: ✅ supported

Target version: 20240203 · Format documentation: https://wezterm.org/config/appearance.html

Verified on: 20260901 · macOS 26.6.2 (2026-11-07)

## Install

Copy umber-calm.toml to ~/.config/wezterm/colors/ and set `config.color_scheme = 'Umber Calm'` in wezterm.lua.

## Uninstall

Remove the color_scheme line and the file.

## Verification checklist

- [ ] background and text
- [ ] 16 ANSI colors (run a color test script)
- [ ] selection
- [ ] cursor and cursor text
- [ ] tab bar: active tab amber, inactive muted

## Verification

Current digest: `sha256:a8fbc485f7f2c9342cef578cbd02b2acafcc9e3d814eb5728a2591050979a101`

Print it yourself with `python3 tools/build.py digest wezterm`. It covers these files:

- `ports/wezterm/umber-calm.toml`

| Date | Result | App version | OS | OS version | Note | Evidence | Digest |
|---|---|---|---|---|---|---|---|
| 2026-11-07 | ✅ verified | 20260901 | macOS | 26.6.2 | Nightly 20260901-002820-4fbd6b8e: resolved palette equals the port; checked by the maintainer in his own WezTerm. |  | `a8fbc485f7f2` |
| 2026-09-28 | ✅ verified | 20260901 | macOS | 26.6.2 | Nightly 20260901-002820-4fbd6b8e. Pixel-sampled: 16 ANSI, bg, selection, cursor, tab bar match the port hex. |  | `2ef53e6927a3` |

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
