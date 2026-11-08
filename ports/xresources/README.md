# Xresources (xterm, urxvt; st with the xresources patch) — Umber Calm

Tier: 🧪 experimental

Target version: X11 · Format documentation: https://invisible-island.net/xterm/manpage/xterm.html

Verified on: —

## Install

Append umber-calm.Xresources to ~/.Xresources (or #include it) and run `xrdb -merge ~/.Xresources`; open a new terminal window. st reads these resources only when built with the xresources patch (https://st.suckless.org/patches/xresources/).

## Uninstall

Remove the lines or the #include and run xrdb again.

## Verification checklist

- [ ] background and text
- [ ] 16 ANSI colors
- [ ] cursor
- [ ] selection background and selected text

## Verification

Current digest: `sha256:7f9c13453c88708ff19f043156603b4cab9152b859a8c941985c89bb28752f46`

Print it yourself with `python3 tools/build.py digest xresources`. It covers these files:

- `ports/xresources/umber-calm.Xresources`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
