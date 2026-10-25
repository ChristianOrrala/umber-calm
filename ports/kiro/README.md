# Kiro IDE — Umber Calm

Tier: 🧪 experimental

Target version: 1.4.26 · Format documentation: https://kiro.dev/docs/upgrade-guides/migrating-from-vscode/

Verified on: —

## Install

For Kiro IDE 1.4 or newer. Download umber-calm-kiro-<version>.vsix from the latest release and run `kiro --install-extension umber-calm-kiro-<version>.vsix` (or Extensions → ⋯ → Install from VSIX…), then pick Umber Calm with Cmd/Ctrl+K Cmd/Ctrl+T. It ships the VS Code port's theme file unchanged; if you imported the VS Code Umber Calm extension, uninstall it first, since both themes are named Umber Calm.

## Uninstall

Uninstall Umber Calm for Kiro from the Extensions view.

## Verification checklist

- [ ] editor, sidebar, tabs and status bar match the VS Code port (same colors)
- [ ] syntax: keywords gold, functions teal-slate, types sea-green, strings olive, constants mauve, operators tan, comments muted
- [ ] agent chat: message and code backgrounds warm, tooltips on surface, no cool gray or bright blue
- [ ] agent status icons: in progress blue, accepted green, input needed yellow, error red
- [ ] chat toggles and pills: active state on the overlay, not orange
- [ ] Agent Focus window: background, sidebar, primary buttons blue, secondary text readable
- [ ] diff review: changed lines on the 12% tints, changed words on the 22% tints, comments readable on both
- [ ] menus, quick pick, keybinding labels and dialogs on surface

## Verification

Current digest: `sha256:a6af61b7219b1fab0519e45e40cdb1fa964a637c96b5a19422cf86a1b6f160b0`

Print it yourself with `python3 tools/build.py digest kiro`. It covers these files:

- `ports/kiro/package.json`
- `ports/vscode/themes/umber-calm-color-theme.json`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
