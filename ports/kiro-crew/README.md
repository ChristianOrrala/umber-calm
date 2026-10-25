# Kiro Crew — Umber Calm

> ⚠️ **Warning:** Kiro Crew paints code blocks (highlight.js, One Dark) and code and diff views (Shiki, pierre-dark) with fixed syntax colors that no theme pack can change; only comments, JSON tool details and the git panel diff follow the palette. The accent (blue) also draws its global keyboard-focus outline and terminal cursor; only text fields take the orange focus ring. The terminal derives black (the background) and the bright colors itself.

Tier: 🧪 experimental

Target version: 0.9.0 · Format documentation: https://github.com/kirodotdev/KiroCrew/blob/v0.9.0/website/docs/theming-contract.md

Verified on: —

## Install

A level-0 theme pack (theme.json and variables.json) for the Kiro Crew dashboard. Unzip umber-calm-kiro-crew-<version>.zip from the latest release (or use ports/kiro-crew/ from a clone), then in Settings → Display → Theme choose Local folder, enter that folder's path and click Install. Set the mode to Dark: Umber Calm has no light variant, so the pack's light block repeats the dark palette.

## Uninstall

Choose another theme in Settings → Display → Theme, then delete ~/.kiro/crew/themes/umber-calm/ (or call DELETE /api/themes/umber-calm).

## Verification checklist

- [ ] the pack installs from a local folder with no validation error
- [ ] chat and pages on bg; cards, inputs, menus and side panels one step lighter (surface)
- [ ] primary buttons, links and the active tab are blue with dark text; text fields take the orange focus ring and nothing else is orange
- [ ] secondary text, timestamps and labels readable on bg and on cards
- [ ] input, dropdown and card borders visible (3:1 on the page)
- [ ] selected rows and text selection use the overlay, hovered rows a quieter step
- [ ] status colors: success green, warning and agent questions yellow, errors red, info blue, agent highlights mauve
- [ ] git panel and file tree: added counts and files green, deleted red
- [ ] JSON tool details: keys text, strings olive, numbers and booleans mauve
- [ ] terminal: ANSI red, green, yellow, blue, magenta and cyan match the palette

## Verification

Current digest: `sha256:1390e083d1d655c922521c6be2999bd2de6cc16cdedec2b06212662795452852`

Print it yourself with `python3 tools/build.py digest kiro-crew`. It covers these files:

- `ports/kiro-crew/theme.json`
- `ports/kiro-crew/variables.json`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
