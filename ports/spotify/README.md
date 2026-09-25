# Spotify (Spicetify) — Umber Calm

> 🟡 **Candidate:** Not yet pinned to exact Spicetify and Spotify client versions.

> ⚠️ **Warning:** requires Spicetify, an unofficial Spotify client modification

Tier: 🟡 candidate

Target version: unpinned: needs the exact Spicetify version and the Spotify client version it was tested on · Format documentation: https://spicetify.app/docs/development/themes

Verified on: —

## Install

Add the [UmberCalm] section of color.ini to your Spicetify theme's color.ini, then `spicetify config color_scheme UmberCalm && spicetify apply`.

## Uninstall

Switch color_scheme back and run `spicetify apply` (or `spicetify restore`).

## Verification checklist

- [ ] main and sidebar backgrounds
- [ ] text and subtext
- [ ] buttons
- [ ] selected row

## Verification

Current digest: `sha256:9d1d4e2ce7c94f79d9214f4aa81fb158db03ef529d46f0f715702bf4fef662b8`

Print it yourself with `python3 tools/build.py digest spotify`. It covers these files:

- `ports/spotify/color.ini`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
