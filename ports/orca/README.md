# Orca — Umber Calm

Tier: 🧪 experimental

Target version: main (fca1d7b) · Minimum version: 1.4.246 · Format documentation: https://github.com/stablyai/orca/blob/main/docs/reference/plugin-themes.md

Verified on: —

## Install

The folder is an Orca plugin. Keep a copy of it (or unzip umber-calm-orca-<version>.zip into a new folder), then in Orca open Settings → Plugins, turn on plugins, choose Development folders… and add that folder (or run `orca plugin dev load <folder>`). Pick Umber Calm as the Dark theme in Settings → Appearance and as the terminal theme in Settings → Terminal. Umber Calm is dark only, so it shows while Orca is in dark mode.

## Uninstall

Pick other themes in Appearance and Terminal, then remove the folder under Settings → Plugins → Development folders… (or run `orca plugin dev unload <folder>`).

## Verification checklist

- [ ] window, editor and terminals on bg with warm text; both sidebars and the tab strip a step darker; cards, menus and popovers a step lighter
- [ ] focus rings, the active tab line and the terminal cursor are orange; nothing else is
- [ ] workspace sidebar: hovered rows a step lighter, the current workspace on the selection color, host badges readable on every row
- [ ] secondary text readable: inactive tabs, descriptions, settings help
- [ ] inputs, switches and checkboxes have visible borders; primary buttons light with dark text
- [ ] editor: keywords gold, functions teal-slate, types sea-green, strings olive, constants mauve, operators tan, comments muted italic
- [ ] diffs: changed lines on the light tint, changed words and the gutter stronger; Source Control file statuses (added and untracked green, modified blue, deleted red, ignored muted)
- [ ] agent chat: your messages on a soft band, code on the background, bold text brighter, links blue, selection readable
- [ ] terminal: 16 ANSI colors, selection

## Verification

Current digest: `sha256:784b295cba5422df21e477c410b8a8f0af91d1c2a73e36db6824e28320330121`

Print it yourself with `python3 tools/build.py digest orca`. It covers these files:

- `ports/orca/orca-plugin.json`
- `ports/orca/terminal/umber-calm.json`
- `ports/orca/themes/umber-calm.json`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
