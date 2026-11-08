# qt5ct / qt6ct — Umber Calm

> 🟡 **Candidate:** The QPalette role order could not be confirmed from official documentation.

Tier: 🟡 candidate

Target version: qt6ct 0.9 · Format documentation: https://github.com/trialuser02/qt6ct

Verified on: —

## Install

Copy umber-calm.conf to ~/.config/qt5ct/colors/ and ~/.config/qt6ct/colors/, set QT_QPA_PLATFORMTHEME=qt5ct (or qt6ct), and pick the scheme in the qt5ct/qt6ct app.

## Uninstall

Pick another scheme and delete the file.

## Verification checklist

- [ ] window and base backgrounds
- [ ] text
- [ ] highlight and highlighted text
- [ ] disabled text

## Verification

Current digest: `sha256:2608019f3897e981d3be89f9c53e99460639bbda4099904a184ade82b9386e16`

Print it yourself with `python3 tools/build.py digest qt5ct`. It covers these files:

- `ports/qt5ct/umber-calm.conf`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
