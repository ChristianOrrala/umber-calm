# Kiro IDE — Umber Calm

Tier: ✅ supported

Target version: 1.4.26 · Format documentation: https://kiro.dev/docs/upgrade-guides/migrating-from-vscode/

Verified on: 1.4.86 · macOS 26.6.2 (2026-11-05)

## Install

For Kiro IDE 1.4 or newer. Install Umber Calm for Kiro from Open VSX (Extensions view, search "Umber Calm for Kiro"), or download umber-calm-kiro-<version>.vsix from the latest release and run `kiro --install-extension umber-calm-kiro-<version>.vsix`; then pick Umber Calm with Cmd/Ctrl+K Cmd/Ctrl+T. It ships the VS Code port's theme file unchanged; if you imported the VS Code Umber Calm extension, uninstall it first, since both themes are named Umber Calm.

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

Current digest: `sha256:ce445867b36e35d88700280992e2ac82399b953a5f5cae33caa102f920b8b242`

Print it yourself with `python3 tools/build.py digest kiro`. It covers these files:

- `assets/marketplace/icon.png`
- `ports/kiro/package.json`
- `ports/vscode/themes/umber-calm-color-theme.json`

| Date | Result | App version | OS | OS version | Note | Evidence | Digest |
|---|---|---|---|---|---|---|---|
| 2026-11-05 | ✅ verified | 1.4.86 | macOS | 26.6.2 | Kiro 1.4.86, clean profile, 0.4.0 vsix: 484/489 colors resolve exactly over CDP (5 VS Code-only chat keys unregistered); theme unchanged since 0.3.0 |  | `ce445867b36e` |
| 2026-11-02 | ✅ verified | 1.4.26 | macOS | 26.6.2 | Kiro 1.4.26, clean profile, 0.3.0 vsix: 484/489 colors resolve exactly over CDP (5 VS Code-only chat keys unregistered); theme unchanged since 0.2.1 |  | `0acd3c6271db` |
| 2026-10-25 | ✅ verified | 1.4.26 | macOS | 26.6.2 | Kiro 1.4.26: 474/489 colors resolve exactly over CDP (5 are 1.140-only chat keys, 10 git decoration keys not registered); syntax; agent chat and approvals confirmed in the app. |  | `dc282dab7dc4` |
| 2026-10-25 | ✅ verified | 1.4.26 | Linux | 24.04 | Ubuntu 24.04, Xvfb: 484/489 colors resolve exactly (5 are 1.140-only chat keys); syntax; diff tints; agent chat icons, toggles, tooltips; Agent Focus; menus. |  | `0bb7f061e6bd` |
| 2026-10-25 | ✅ verified | 1.4.26 | Linux | 24.04 | Ubuntu 24.04, Xvfb: 484/489 colors resolve exactly (5 are 1.140-only chat keys); syntax; diff tints; agent chat icons, toggles, tooltips; Agent Focus; menus. |  | `a6af61b7219b` |

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
