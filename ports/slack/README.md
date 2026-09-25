# Slack — Umber Calm

Tier: 🧪 experimental

Target version: 4.41 · Format documentation: https://slack.com/help/articles/205166337-Change-your-Slack-theme

Verified on: —

## Install

In Slack: Preferences → Appearance → Custom theme → Import theme, then paste the line from umber-calm.txt (a legacy 8-color theme string). Slack only themes the sidebar and may merge some of the eight slots.

## Uninstall

Pick another theme.

## Verification checklist

- [ ] import accepted
- [ ] sidebar background
- [ ] active and hovered items
- [ ] mention badge
- [ ] presence dot
- [ ] which of the 8 slots Slack applied

## Verification

Current digest: `sha256:aeb155227e303b9d57fc75cd3b5e240bafbd641b80773cb1c228741ed9ce736e`

Print it yourself with `python3 tools/build.py digest slack`. It covers these files:

- `ports/slack/umber-calm.txt`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
