# GTK 3/4 + libadwaita — Umber Calm

Tier: 🧪 experimental

Target version: libadwaita 1.6 · Format documentation: https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/

Verified on: —

## Install

Copy gtk.css to ~/.config/gtk-4.0/gtk.css (and ~/.config/gtk-3.0/gtk.css), then restart GTK apps. Partial by nature: it only overrides libadwaita's named colors.

## Uninstall

Delete the gtk.css files (or remove the @define-color lines).

## Verification checklist

- [ ] window and view backgrounds
- [ ] header bars
- [ ] sidebars and cards
- [ ] accent and destructive colors

## Verification

Current digest: `sha256:75042c4bc7955d87efbad65df76408e1ba1cb6094c0d4026e86fbd0b082b3194`

Print it yourself with `python3 tools/build.py digest gtk`. It covers these files:

- `ports/gtk/gtk.css`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
