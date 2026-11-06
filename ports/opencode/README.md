# OpenCode — Umber Calm

> ⚠️ **Warning:** OpenCode draws the main prompt's cursor in the text color and its bar in the agent's color, so neither is orange; dialogs, forms and the selected file are. It paints code builtins, built-in types and tags with its error color, so `string`, `null` and `<div>` are red in code, and it draws the markdown rule in a fixed gray. The file is a v2 theme document, which OpenCode reads but does not document yet; OpenCode 1 cannot read it.

Tier: 🧪 experimental

Target version: 2.2.5 · Format documentation: https://github.com/anomalyco/opencode/blob/v2.2.5/packages/theme/src/tui/schema.ts

Verified on: —

## Install

Needs OpenCode 2 (`opencode --version`). Copy umber-calm.json to ~/.config/opencode/themes/ and pick umber-calm with the /theme command, or set `"theme": {"name": "umber-calm"}` in ~/.config/opencode/cli.json. It stays dark in a light terminal.

## Uninstall

Pick another theme and delete the file.

## Verification checklist

- [ ] theme loads, and stays dark in a light terminal
- [ ] session: background, text, muted text, tool blocks, prompt
- [ ] dialogs (/theme, /models): panel, active row orange with dark text, current item green, nothing else orange
- [ ] tool output and diffs: added and removed lines, signs, line numbers
- [ ] syntax roles and markdown in replies
- [ ] session tabs: unread and attention blue, running number yellow
- [ ] questions and permission forms: focused row orange, picked item green
- [ ] embedded terminal: ANSI colors match the table in the style guide

## Verification

Current digest: `sha256:dd26b6ee09dd5eb961c70948d6b9fedf8ee6a9b2c6adbbe90371ec2cf539ed03`

Print it yourself with `python3 tools/build.py digest opencode`. It covers these files:

- `ports/opencode/umber-calm.json`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
