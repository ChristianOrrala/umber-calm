# VS Code — Umber Calm

Tier: 🧪 experimental

Target version: 1.95 · Minimum version: 1.95.0 · Format documentation: https://code.visualstudio.com/api/extension-guides/color-theme

Verified on: —

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

Current digest: `sha256:8e20fa1f8675f7ea0eaa823cc5ee6b41ee90db8f0c0609c86f6f53aa5d79bf08`

Print it yourself with `python3 tools/build.py digest vscode`. It covers these files:

- `ports/vscode/package.json`
- `ports/vscode/themes/umber-calm-color-theme.json`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
