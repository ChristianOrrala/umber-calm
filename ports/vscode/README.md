# VS Code — Umber Calm

Tier: ✅ supported

Target version: 1.95 · Minimum version: 1.95.0 · Format documentation: https://code.visualstudio.com/api/extension-guides/color-theme

Verified on: 1.143.1 · macOS 26.6.2 (2026-10-25)

## Install

Install Umber Calm from the VS Code Marketplace (Extensions view, search "Umber Calm"), or download umber-calm-<version>.vsix from the latest release and run `code --install-extension umber-calm-<version>.vsix`; then pick Umber Calm with Cmd/Ctrl+K Cmd/Ctrl+T.

## Uninstall

Uninstall the Umber Calm extension from the Extensions view.

## Verification checklist

- [ ] editor background, text, current line
- [ ] syntax: keywords gold, functions teal-slate, types sea-green, strings olive, constants mauve, operators tan, comments muted
- [ ] style guide rules: typeof/in/new/and/not gold, => and brackets tan, const bindings and JSON keys in text color, self mauve
- [ ] selection, word highlights and find matches (current match solid gold with dark text)
- [ ] cursor amber; focus outlines amber and visible on panels; nothing else amber
- [ ] tabs: active tab has an amber top border
- [ ] sidebar (hovered rows visible), status bar, panel
- [ ] inputs, dropdowns and checkboxes have visible borders
- [ ] diff editor: changed lines on the light tint, changed words on the full tint
- [ ] breadcrumbs and outline symbol icons in syntax colors, light bulb gold
- [ ] integrated terminal ANSI colors

## Verification

Current digest: `sha256:63402f4907bfbb44eaad12dbb08016fa518017a13db9e183cdee469a3b6ad4f8`

Print it yourself with `python3 tools/build.py digest vscode`. It covers these files:

- `assets/marketplace/icon.png`
- `ports/vscode/package.json`
- `ports/vscode/themes/umber-calm-color-theme.json`

| Date | Result | App version | OS | OS version | Note | Evidence | Digest |
|---|---|---|---|---|---|---|---|
| 2026-10-25 | ✅ verified | 1.143.1 | macOS | 26.6.2 | VS Code 1.143.1, clean profile: 489/489 theme colors resolve exactly over CDP; syntax tokens; amber cursor. 1.143 hides the active tab top border in its new tab style. |  | `63402f4907bf` |
| 2026-10-25 | ✅ verified | 1.140 | Linux | 24.04 | VSCodium 1.140.06880, Ubuntu 24.04, Xvfb: 489/489 theme colors resolve exactly over CDP; style-guide tokens in TS, Python, JSON, CSS; diff tints; tab border; ANSI. |  | `8f793848e649` |
| 2026-10-25 | ✅ verified | 1.140 | Linux | 24.04 | VSCodium 1.140.06880, Ubuntu 24.04, Xvfb: 489/489 theme colors resolve exactly over CDP; style-guide tokens in TS, Python, JSON, CSS; diff tints; tab border; ANSI. |  | `fed6095242ee` |
| 2026-09-28 | ✅ verified | 1.139.1 | macOS | 26.6.2 | Full checklist after the find-foreground fix. Active tab top border shows with workbench.experimental.modernUI off; 1.139's default modern tabs hide it for every theme. |  | `0246d948acbe` |

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
