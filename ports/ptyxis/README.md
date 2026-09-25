# Ptyxis — Umber Calm

> 🟡 **Candidate:** The value syntax of .palette files could not be confirmed from official documentation.

Tier: 🟡 candidate

Target version: 47 · Format documentation: https://gitlab.gnome.org/chergert/ptyxis

Verified on: —

## Install

Copy umber-calm.palette to ~/.local/share/org.gnome.Ptyxis/palettes/ and pick Umber Calm in Preferences. The file sets the cursor color; no selection key is known, so selection follows Ptyxis's default.

## Uninstall

Pick another palette and delete the file.

## Verification checklist

- [ ] palette appears in Preferences
- [ ] background, text, 16 ANSI colors
- [ ] cursor color
- [ ] selection readable (inherited)

## Verification

Current digest: `sha256:3c3ad48e75aefe071ab1f3321dca4ef3f35e2d28b65b68eed3705b86a7857990`

Print it yourself with `python3 tools/build.py digest ptyxis`. It covers these files:

- `ports/ptyxis/umber-calm.palette`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
