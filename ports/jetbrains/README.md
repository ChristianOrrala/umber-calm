# JetBrains IDEs — Umber Calm

## Known limitations

The editor scheme sets every `DefaultLanguageHighlighterColors` key and every language key that Darcula colors explicitly for Java, Kotlin, Python and Markdown (IntelliJ Platform 2024.3; `tests/fixtures/jetbrains-darcula-language-keys.txt`). These language keys still inherit Darcula's colors:

- **JavaScript and TypeScript:** their keys come from the bundled, closed-source JavaScript plugin, whose Darcula colors are not published. The verification checklist checks JavaScript by eye; a key found in a Darcula color is added to the scheme and to the fixture.
- **Every other language plugin** (for example Go, Rust, SQL, YAML, shell scripts, Groovy): keys that its own Darcula file colors explicitly keep those colors.

Tier: 🧪 experimental

Target version: 2024.3 · Minimum version: 2024.3 · Format documentation: https://plugins.jetbrains.com/docs/intellij/theme-structure.html

Verified on: —

## Install

Download umber-calm-jetbrains-<version>.jar from the release, then Settings → Plugins → ⚙ → Install Plugin from Disk…, restart, and choose Umber Calm under Appearance.

## Uninstall

Settings → Plugins → Umber Calm → Uninstall.

## Verification checklist

- [ ] UI background and text
- [ ] editor background, caret, selection
- [ ] syntax roles in Java, Kotlin, Python and Markdown (no Darcula colors left)
- [ ] JavaScript: note any token still in a Darcula color (known limitation; map it in the next release)
- [ ] tool windows and tabs
- [ ] inlay hints

## Verification

Current digest: `sha256:860671984433d030296bbba59fd8127e225d8fcdcdd019d4dd6df8971cc7f8d8`

Print it yourself with `python3 tools/build.py digest jetbrains`. It covers these files:

- `ports/jetbrains/META-INF/plugin.xml`
- `ports/jetbrains/UmberCalm.theme.json`
- `ports/jetbrains/UmberCalm.xml`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
