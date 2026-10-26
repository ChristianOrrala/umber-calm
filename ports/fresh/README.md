# Fresh — Umber Calm

> ⚠️ **Warning:** Fresh leaves the cursor color to the terminal: the cursor is orange when the terminal runs Umber Calm (or sets an orange cursor), whatever the theme says.

Tier: 🧪 experimental

Target version: 0.5.4 · Format documentation: https://github.com/sinelaw/fresh/blob/v0.5.4/docs/features/themes.md

Verified on: —

## Install

Copy umber-calm.json to ~/.config/fresh/themes/ and set `"theme": "umber-calm.json"` in ~/.config/fresh/config.json (or pick Umber Calm from Ctrl+P, Select Theme).

## Uninstall

Pick another theme and delete the file.

## Verification checklist

- [ ] editor background, text and current line
- [ ] cursor orange in the focused split (from the terminal theme), a dim block with readable text in the others
- [ ] active tab orange, inactive tabs readable, nothing else orange
- [ ] syntax roles
- [ ] brackets quiet with rainbow brackets on, matched pair bold and underlined
- [ ] selection, search matches (all and current), and word occurrences underlined on a soft band with the current line unbroken
- [ ] diagnostics on code and in the status bar
- [ ] diff and git review: lines and changed words
- [ ] menus, command palette, popups, completion, help and settings readable
- [ ] file explorer git status
- [ ] embedded terminal

## Verification

Current digest: `sha256:97e2ef9cc126e4f269fa87bb17c99b7f427ef0fc7e378cdd44197667e87ef282`

Print it yourself with `python3 tools/build.py digest fresh`. It covers these files:

- `ports/fresh/umber-calm.json`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
