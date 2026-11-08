# Moshi — Umber Calm

A theme for [Moshi](https://getmoshi.app), the SSH and Mosh terminal for iPhone and iPad. Moshi colors its own screens from the theme too, so the session list, the connection cards and the keyboard bar wear Umber Calm as well as the terminal. Which of the 16 colors each of those controls uses is Moshi's choice.

<img src="umber-calm-qr.svg" width="232" alt="QR code that imports Umber Calm into Moshi">

The QR code holds a `moshi://theme` link with the theme inside. `umber-calm-import.txt` holds the same theme as a `moshi-theme:` string for pasting, and `umber-calm.json` is the theme itself, which Moshi also accepts pasted as text.

Tier: 🧪 experimental (the last verification was for an earlier revision of these files)

Target version: 3.2.2 · Format documentation: https://getmoshi.app/docs/personalization

Verified on: 3.2.2 · iOS 27.3 (2026-11-02)

## Install

In Moshi, open Settings → Theme → Import theme and scan the QR code above with the import screen's camera (the system camera works too). On the phone itself, copy the line in umber-calm-import.txt instead and paste it on the import screen. Then choose Umber Calm in Settings → Theme.

## Uninstall

Choose another theme in Settings → Theme.

## Verification checklist

- [ ] terminal background and text
- [ ] 16 ANSI colors
- [ ] selection
- [ ] cursor is orange (focus)
- [ ] Moshi's own screens (session list, connection cards, settings, keyboard bar) readable

## Verification

Current digest: `sha256:ca6dce14efbc680ebc4d4fa7148b92a51225bf89b74e4f92f9741df5dcb328f8`

Print it yourself with `python3 tools/build.py digest moshi`. It covers these files:

- `ports/moshi/umber-calm-import.txt`
- `ports/moshi/umber-calm-qr.svg`
- `ports/moshi/umber-calm.json`

| Date | Result | App version | OS | OS version | Note | Evidence | Digest |
|---|---|---|---|---|---|---|---|
| 2026-11-02 | ✅ verified | 3.2.2 | iOS | 27.3 | Developer beta of iOS 27.3; imported by scanning the QR code |  | `448a39ba4619` |

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
