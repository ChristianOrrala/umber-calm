# foot — Umber Calm

Tier: 🧪 experimental

Target version: 1.26.0 · Format documentation: https://man.archlinux.org/man/foot.ini.5.en

Verified on: —

## Install

Requires foot 1.26.0 or newer: the theme uses the [colors-dark] section, which foot added in 1.26.0 (older releases reject it). Copy umber-calm.ini to ~/.config/foot/ and add `include=~/.config/foot/umber-calm.ini` under [main] in foot.ini.

## Uninstall

Remove the include line and the file.

## Verification checklist

- [ ] passes `foot --check-config` on the target version
- [ ] background and text
- [ ] 16 ANSI colors
- [ ] cursor
- [ ] selection
- [ ] URLs

## Verification

Current digest: `sha256:ecacdd9402bcd4994fe19ac0bb3851a29ec5b8e0ab6492039baaed3ef26f6a0d`

Print it yourself with `python3 tools/build.py digest foot`. It covers these files:

- `ports/foot/umber-calm.ini`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
