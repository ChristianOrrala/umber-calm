# Herdr — Umber Calm

> ⚠️ **Warning:** Herdr paints some colors in code that no theme reaches: blocked agents and modified files in red, the commits-behind count in red, space chips in fixed colors (one of them orange) with white letters, the file preview's syntax colors from ANSI slots (keywords purple, numbers red), and disabled controls and a dragged space faded in code. It also draws its one accent, orange here, beyond focus: switches, primary buttons, chosen options and their check marks, palette and help matches, notices, new-update dots and drop markers. Program icons and color-font glyphs keep their own colors.

Tier: 🧪 experimental (the last verification was for an earlier revision of these files)

Target version: 0.1.12 · Format documentation: https://github.com/herdrdev/herdr-app/blob/v0.1.12/defaults/AGENTS.md

Verified on: 0.1.12 · macOS 26.6.2 (2026-11-02)

## Install

Copy umber-calm.json to ~/.config/herdr-app/themes/, then pick umber-calm from the theme list in Settings (or add "theme": "umber-calm" to ~/.config/herdr-app/settings.json). Keep minimum_contrast at 1.

## Uninstall

Pick another theme and delete the file.

## Verification checklist

- [ ] terminals on bg with warm text, sidebars a step darker, menus and popovers a step lighter
- [ ] focused pane border and focused inputs orange; Herdr's other accent marks (switches, primary buttons, chosen options, matches, notices, update dots, drop markers) orange too (known limit); nothing else
- [ ] hover and selected rows warm and distinct in the sidebar, menus and the picker
- [ ] agent states: working yellow spinner, blocked bright red Needs you, done green dot, idle ring
- [ ] secondary labels readable, on selected rows too
- [ ] settings, welcome, help, picker and palette readable
- [ ] Changes panel: diff rows and file statuses
- [ ] file preview

## Verification

Current digest: `sha256:1882b0639fd62481f168ca1efe2951bd6acb483874a62461da45b056dc07d2ec`

Print it yourself with `python3 tools/build.py digest herdr-app`. It covers these files:

- `ports/herdr-app/umber-calm.json`

| Date | Result | App version | OS | OS version | Note | Evidence | Digest |
|---|---|---|---|---|---|---|---|
| 2026-11-02 | ✅ verified | 0.1.12 | macOS | 26.6.2 |  |  | `0f770544524e` |

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
