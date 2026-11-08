# Changelog

## Unreleased

- New port: Orca, pinned to its `main` branch at `fca1d7b` and verified in the app on Orca 1.4.253 and macOS 26.6.2. A content-only Orca plugin: an app theme that sets all 73 public tokens from palette roles and colors code from the syntax roles, plus a matching terminal theme. Sidebars and the tab strip sit a step darker than the editor, with hovered and current rows a step lighter each. Orange marks focus rings, the active tab line and the terminal cursor. Every color pair Orca checks clears its floor, so Orca keeps all of them. Orca 1.4.253 and older skip the seven chat tokens and keep their own chat colors. Some colors stay Orca's choice: the code editor tints selections with the focus ring, so they are orange, and bracket pairs keep Monaco's colors (the port's README lists them).
- Claude Code: text you select with the mouse in fullscreen now sits on the selection color (`#3C3A36`) instead of the base theme's solid ANSI blue. Your messages, `!` commands and `#` notes sit on a purple band (`purple` at 22 %, `#453B41`), so your requests stand apart from replies. The style guide lists the band as a measured state: `text` reads 6.6:1 on it. A selection inside your own messages barely shows on it. Target version is now 2.1.319, the build it was verified on again (macOS 26.6.2).
- Claude Code: the theme now sets 66 of Claude Code's 72 colors instead of 6, so they no longer depend on the terminal's palette. Where there is color, it means something or helps you read. Permission prompts are gold instead of a pale blue; inline code stays the terminal's bright blue, because Claude Code reads it from the base theme, not from a custom theme. Claude's spinner and welcome banner are tan instead of red, which Umber Calm keeps for errors. Secondary text, box borders and the empty part of usage bars step back from body text. Accept edits is orange, plan mode cyan, and the "ultrathink" keyword is one color instead of a rainbow. Purple and pink agents now differ, and an orange agent is orange. The six diff colors stay with the terminal: Claude Code's diff view rounds theme colors to the terminal's 256-color set, so set colors turn into grey row bands and harsher greens and reds. Left unset, the terminal paints them with Umber Calm's own green and red. The mascot and agents you color orange are the only orange outside the active mode. Verified in the app on 2.1.319 and macOS 26.6.2.

## 0.5.0 (2026-11-08)

- Comments and secondary text are slightly lighter (`muted` `#988F7F`, was `#938A7B`): 5.2:1 on the background and 4.6:1 on panels, so they now reach 4.5:1 everywhere and the "comments on panels" exception is gone. The least important text and ANSI bright black are lighter too (`dim_text` `#77726A`, was `#6E6961`): 3.45:1, still a clear step below comments.
- The README recommends fonts: three to try, Regular weight, sized by lowercase height.
- Verified again with the new greys: tmux 3.8, Starship 1.27.0, Zellij 0.45.1, WezTerm, Neovim 0.12.6, VS Code, Kiro, Fresh 0.5.7, Herdr 0.1.13 and OpenCode 2.2.5. Herdr TUI, Moshi and Kiro Crew are experimental until they are checked again.
- Herdr and Fresh: their READMEs now list colors each app paints in its own code (Herdr 0.1.13's find-in-terminal highlight; Fresh's git gutter, `--diff` gutter and embedded terminal).

## 0.4.0 (2026-11-06)

- OpenCode: the port is rebuilt for OpenCode 2 and verified in the app on 2.2.5 and macOS 26.6.2. It is a v2 theme document, so every color it draws comes from the palette instead of scales OpenCode would generate. Orange marks the active row, focused form fields and the selected file; the prompt sits quietly on the panel color, and the embedded terminal gets the ANSI table. OpenCode 1 cannot read this file. Some colors stay OpenCode's choice: its builtins, types and tags use the error color, so `string` and `null` are red in code (the port's README lists them).
- New port: Moshi 3.2.2, the SSH and Mosh terminal for iPhone and iPad, verified in the app on iOS 27.3. It sets every color of Moshi's theme format from the terminal roles, and Moshi colors its own screens from them too. Orange only marks the cursor. Scan the QR code in the port's README from Moshi's import screen, or paste the `moshi-theme:` line next to it.

## 0.3.0 (2026-11-02)

- New port: Fresh 0.5.4, verified in the app on macOS 26.6.2. A standalone theme that sets all 142 colors from palette roles. Orange only marks the cursor and the active tab; brackets stay quiet with rainbow brackets on; occurrences of the word under the cursor are underlined on a soft band. Error text and deleted files use the bright red, which stays readable on selected rows. Fresh leaves the cursor color to the terminal.
- New port: Herdr 0.1.12, the desktop app, verified in the app on macOS 26.6.2. A theme that sets every panel color from palette roles, so none of Herdr's cool defaults show through, with warm see-through hover and selection rows. Orange marks the focused pane, focused inputs and the cursor; blocked agents use the bright red. Some colors are set in Herdr's code and stay as they are (the port's README lists them).
- The herdr port is now named Herdr TUI, as upstream calls it, and links to its new docs page.

## 0.2.1 (2026-10-25)

- VS Code and Kiro: the extensions are published on the VS Code Marketplace and Open VSX as `ChristianOrrala.umber-calm` and `ChristianOrrala.umber-calm-kiro`, with a listing page, an icon and a warm header. If you installed an earlier `.vsix` from a GitHub release, uninstall it first: both are named Umber Calm.
- The `.vsix` files now carry this changelog.

## 0.2.0 (2026-10-25)

- VS Code: the syntax colors now follow the style guide, as the Neovim port already did.
  - Keyword operators (`typeof`, `instanceof`, `in`, `new`; Python `and`, `or`, `not`, `in`, `is`) are keywords.
  - `=>` is an operator.
  - `const` and readonly bindings, JSON keys and CSS properties are variables.
  - CSS units are constants.
  - Python `self` and `cls` are built-ins.
  - Brackets take the operator color at every nesting level.
  - Diff files color added, removed and changed lines.
- VS Code: every workbench color VS Code 1.140 would otherwise fill with a default outside the palette is now set from palette roles. That is about 250 keys, checked by enumerating every resolved color in VSCodium 1.140. They cover icons, progress, menus, quick pick, keybinding labels, validation, symbol icons, the light bulb, the overview ruler and minimap, debugging, testing and coverage, merge conflicts, inline edits, source control graph, chat and badges. Orange no longer appears outside focus (ratings stars, find matches in the overview ruler, class icons), red no longer marks anything but errors and deletions, and the no-folder status bar is no longer purple. Breakpoints are mauve.
- VS Code: diff lines use the 12% tint with changed words on the 22% tint, since VS Code emphasizes changed words. Active toggles are blue instead of orange. List hover is half the overlay, so it shows on the sidebar.
- VS Code: accessibility (WCAG 1.4.11, 3:1 for controls and focus).
  - The focus outline is 60% orange (3.6:1 on panels).
  - Input, dropdown and checkbox borders use `muted` (4.3:1 on panels).
  - Ignored files, ghost text, placeholders and disabled text use `muted` instead of `dim_text`, which drops to 2.7:1 on panels.
- New port: Kiro IDE 1.4.26, as its own extension, `umber-calm-kiro-<version>.vsix`, that ships the VS Code port's theme file unchanged (the colors Kiro's agent chat and Agent Focus read are standard VS Code keys).
- New port: Kiro Crew 0.9.0, a level-0 theme pack that sets all 56 dashboard variables from palette roles. Orange only marks the text-field focus ring. Inputs, dropdowns and card outlines (`--border`) reach 3:1 on the page. Umber Calm has no light variant, so the light block repeats the dark palette. Kiro Crew's code highlighting and its settings icon tiles use fixed colors that no pack can change; the port README says so.
- Tier changes: VS Code stays supported, re-verified on the repaired theme. Kiro IDE and Kiro Crew go from experimental to supported. All three were verified on Ubuntu 24.04: VS Code in VSCodium 1.140 (the same Code OSS theme engine), Kiro IDE 1.4.26, Kiro Crew 0.9.0. Every resolved color was read from the running app, and screenshots were checked against each checklist.

## 0.1.0 (2026-09-29)

- Foundation: palette source of truth, generator with safe writes, checks (formats, readability, wording, repository hygiene), digest-bound verification tiers, release gate, JSON export.
- Tier changes: Neovim, VS Code, WezTerm, tmux, Starship, Zellij and Claude Code go from experimental to supported, each verified in the real app on macOS 26.6.2.
- tmux: hex colors are now lowercase. tmux expands styles as formats, where `#D` and `#F` are aliases, so uppercase values such as `#D6C9B6` broke the copy-mode selection (it was invisible) and the message and status text colors.
- VS Code: the current find match now has dark text on solid gold, and the other matches keep readable text on their tint. VS Code paints the current match with `editor.findMatchHighlightForeground` and the others with `editor.findMatchForeground`, the reverse of what the names suggest.
- New port: herdr 0.9.1, supported (verified in the real app on macOS 26.6.2). Every theme token is set from palette roles; orange only marks focus.
- Claude Code: target version is now 2.1.284, the build it was verified on.
- README: a calm Claude Code session as the hero, a short story of why the palette exists, and a collapsed "See everything at once" section with an editor, a terminal, the full sample render and a color-vision strip. Generated color swatches with what each color is used for, neutral generated badges, and ports grouped by tier with only the supported ones open.
