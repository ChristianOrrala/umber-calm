# GNOME Terminal — Umber Calm

Tier: 🧪 experimental

Target version: 3.54 · Format documentation: https://help.gnome.org/users/gnome-terminal/stable/app-colors.html.en

Verified on: —

## Install

Run `bash install.sh` (needs dconf and python3). It creates the profile "Umber Calm" under its own fixed UUID; profiles it did not create are never changed, even one with the same name. Re-running updates it.

## Uninstall

Run `bash install.sh --remove`. If Umber Calm is your default profile, the first remaining profile becomes the default; if it is your only profile, create another one first.

## Verification checklist

- [ ] new profile exists and is selectable
- [ ] background, text, 16 ANSI colors
- [ ] cursor and selection
- [ ] re-running does not duplicate the profile
- [ ] --remove deletes only this profile

## Verification

Current digest: `sha256:483e82f0dd6ca27b25f34f0784d475c3b34012a90893d32d29aea0e1027c92e8`

Print it yourself with `python3 tools/build.py digest gnome-terminal`. It covers these files:

- `ports/gnome-terminal/install.sh`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
