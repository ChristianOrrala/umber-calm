# Firefox — Umber Calm

Tier: 🧪 experimental

Target version: 133 · Format documentation: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme

Verified on: —

## Install

Until the theme is signed on addons.mozilla.org: open about:debugging → This Firefox → Load Temporary Add-on… and pick manifest.json (it lasts until restart).

## Uninstall

Remove it in about:addons (or restart for the temporary add-on).

## Verification checklist

- [ ] tab strip and selected tab (focus-color line)
- [ ] toolbar and URL field
- [ ] popups and sidebar
- [ ] new tab page

## Verification

Current digest: `sha256:e03e2678c5a4eef512e6a0fcc74b2f969ec53a2c7b911a208cb0bc911c2cb86d`

Print it yourself with `python3 tools/build.py digest firefox`. It covers these files:

- `ports/firefox/manifest.json`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
