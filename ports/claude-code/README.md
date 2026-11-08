# Claude Code — Umber Calm

Tier: ✅ supported

Target version: 2.1.319 · Format documentation: https://code.claude.com/docs/en/terminal-config

Verified on: 2.1.319 · macOS 26.6.2 (2026-11-08)

## Install

Copy umber-calm.json to ~/.claude/themes/ and select it with /theme (custom:umber-calm). It builds on the dark-ansi base, so use it together with an Umber Calm terminal port.

## Uninstall

Pick another theme with /theme and delete the file.

## Verification checklist

- [ ] your messages, ! commands and # notes on the purple band (#453B41), set apart from replies, the same when hovered
- [ ] composerSidebarBackground visibly applied: the diff side panel is the surface color, not gray
- [ ] diff +/− counts readable (green/red)
- [ ] no gray bands on added rows
- [ ] fullscreen mouse selection on the selection color (not blue), selected text readable

## Verification

Current digest: `sha256:585c50d34a69ad66bfac69745e0bee9a01b697b3aba3e57c19a25b1e675767a9`

Print it yourself with `python3 tools/build.py digest claude-code`. It covers these files:

- `ports/claude-code/umber-calm.json`

| Date | Result | App version | OS | OS version | Note | Evidence | Digest |
|---|---|---|---|---|---|---|---|
| 2026-11-08 | ✅ verified | 2.1.319 | macOS | 26.6.2 | Owner screenshots in Orca: messages #453B41, diff panel #2A2826, no row bands, +/- #B9C684/#EC9A8C, selection #3C3A36. ! and # share the value, not on screen. |  | `585c50d34a69` |
| 2026-09-28 | ✅ verified | 2.1.284 | macOS | 26.6.2 | Owner screenshots: user messages #201F1D, diff panel #2A2826 with no row bands, +/- counts #B9C684/#EC9A8C. |  | `69ea78169c34` |

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
