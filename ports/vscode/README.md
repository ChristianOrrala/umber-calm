# VS Code — Umber Calm

Tier: ✅ supported

Target version: 1.95 · Minimum version: 1.95.0 · Format documentation: https://code.visualstudio.com/api/extension-guides/color-theme

Verified on: 1.139.1 · macOS 26.6.2 (2026-09-28)

## Install

Download umber-calm-<version>.vsix from the latest release and run `code --install-extension umber-calm-<version>.vsix`, then pick Umber Calm with Cmd/Ctrl+K Cmd/Ctrl+T.

## Uninstall

Uninstall the Umber Calm extension from the Extensions view.

## Verification checklist

- [ ] editor background, text, current line
- [ ] syntax: keywords gold, functions teal-slate, types sea-green, strings olive, constants mauve, operators tan, comments muted
- [ ] selection, word highlights and find matches (current match solid gold with dark text)
- [ ] cursor amber
- [ ] tabs: active tab has an amber top border
- [ ] sidebar, status bar, panel
- [ ] diff editor
- [ ] integrated terminal ANSI colors

## Verification

Current digest: `sha256:0246d948acbe7732ed2d872e1c2e086ab8682cd0f298886d51bd2ef013ebc1ee`

Print it yourself with `python3 tools/build.py digest vscode`. It covers these files:

- `ports/vscode/package.json`
- `ports/vscode/themes/umber-calm-color-theme.json`

| Date | Result | App version | OS | OS version | Note | Evidence | Digest |
|---|---|---|---|---|---|---|---|
| 2026-09-28 | ✅ verified | 1.139.1 | macOS | 26.6.2 | Full checklist after the find-foreground fix. Active tab top border shows with workbench.experimental.modernUI off; 1.139's default modern tabs hide it for every theme. |  | `0246d948acbe` |

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
