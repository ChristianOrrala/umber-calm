# Claude Code — Umber Calm

> ⚠️ **Warning:** Claude Code paints some colors outside the theme's reach. Inline code in replies takes its color from the base theme by name, so it stays the terminal's bright blue (#9DC2C5) whatever the theme sets (https://github.com/anthropics/claude-code/issues/98920). Its diff view rounds theme colors to the terminal's 256-color set, which turns tinted rows into the same grey and shifts green and red, so the theme leaves the six diff colors to the terminal, which paints them in Umber Calm's green and red (https://github.com/anthropics/claude-code/issues/85660). The mascot and agents you color orange are orange outside focus.

Tier: ✅ supported

Target version: 2.1.319 · Format documentation: https://code.claude.com/docs/en/terminal-config

Verified on: 2.1.319 · macOS 26.6.2 (2026-11-08)

## Install

Copy umber-calm.json to ~/.claude/themes/ and select it with /theme (custom:umber-calm). It builds on the dark-ansi base, so use it together with an Umber Calm terminal port.

## Uninstall

Pick another theme with /theme and delete the file.

## Verification checklist

- [ ] your messages, ! commands and # notes a step darker than the transcript (#1A1917), set apart from replies, the same when hovered
- [ ] composerSidebarBackground visibly applied: the diff side panel is the surface color, not gray
- [ ] diff +/− counts readable (green/red)
- [ ] diff rows without grey bands; changed words on Umber Calm's bright green and red (#B9C684, #EC9A8C), not #AFD787 or #FF8787
- [ ] fullscreen mouse selection on the selection color (not blue), selected text readable
- [ ] permission prompts gold (inline code stays the terminal's bright blue, #9DC2C5); accept edits orange, plan mode cyan
- [ ] Claude's spinner and welcome banner tan, the mascot orange; secondary text and box borders quieter than body text

## Verification

Current digest: `sha256:218fc2635f32214aca207e5425efb8221dc7c2d7f9a910f0598e0aaa220d28d7`

Print it yourself with `python3 tools/build.py digest claude-code`. It covers these files:

- `ports/claude-code/umber-calm.json`

| Date | Result | App version | OS | OS version | Note | Evidence | Digest |
|---|---|---|---|---|---|---|---|
| 2026-11-08 | ✅ verified | 2.1.319 | macOS | 26.6.2 | Owner checked in the app: messages and ! commands on #1A1917, a step below the transcript. # notes share the value. The rest is unchanged since the full check. |  | `218fc2635f32` |
| 2026-11-08 | ✅ verified | 2.1.319 | macOS | 26.6.2 | Owner checked every checklist item in Orca. Screenshots: prompt chip #DCC07D, accept edits #EDA97C, prompt border #77726A, /diff rows unbanded, markers #B9C684/#EC9A8C. |  | `e6ebcfbc77a9` |
| 2026-11-08 | ✅ verified | 2.1.319 | macOS | 26.6.2 | Owner screenshots in Orca: prompt chip #DCC07D, accept edits #EDA97C, prompt border #77726A, /diff rows unbanded, markers #B9C684/#EC9A8C. Plan mode, spinner, mascot not captured. |  | `e6ebcfbc77a9` |
| 2026-11-08 | ✅ verified | 2.1.319 | macOS | 26.6.2 | Owner screenshots in Orca: messages #453B41, diff panel #2A2826, no row bands, +/- #B9C684/#EC9A8C, selection #3C3A36. ! and # share the value, not on screen. |  | `585c50d34a69` |
| 2026-09-28 | ✅ verified | 2.1.284 | macOS | 26.6.2 | Owner screenshots: user messages #201F1D, diff panel #2A2826 with no row bands, +/- counts #B9C684/#EC9A8C. |  | `69ea78169c34` |

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
