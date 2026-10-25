# Changelog

## Unreleased

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
- New port: Kiro IDE 1.4.26 (experimental), as its own extension, `umber-calm-kiro-<version>.vsix`, that ships the VS Code port's theme file unchanged (the colors Kiro's agent chat and Agent Focus read are standard VS Code keys).
- New port: Kiro Crew 0.9.0 (experimental), a level-0 theme pack that sets all 56 dashboard variables from palette roles. Orange only marks the text-field focus ring. Inputs, dropdowns and card outlines (`--border`) reach 3:1 on the page. Umber Calm has no light variant, so the light block repeats the dark palette. Kiro Crew's code highlighting uses fixed syntax colors that no pack can change; the port README says so.

## 0.1.0 (2026-09-29)

- Foundation: palette source of truth, generator with safe writes, checks (formats, readability, wording, repository hygiene), digest-bound verification tiers, release gate, JSON export.
- Tier changes: Neovim, VS Code, WezTerm, tmux, Starship, Zellij and Claude Code go from experimental to supported, each verified in the real app on macOS 26.6.2.
- tmux: hex colors are now lowercase. tmux expands styles as formats, where `#D` and `#F` are aliases, so uppercase values such as `#D6C9B6` broke the copy-mode selection (it was invisible) and the message and status text colors.
- VS Code: the current find match now has dark text on solid gold, and the other matches keep readable text on their tint. VS Code paints the current match with `editor.findMatchHighlightForeground` and the others with `editor.findMatchForeground`, the reverse of what the names suggest.
- New port: herdr 0.9.1, supported (verified in the real app on macOS 26.6.2). Every theme token is set from palette roles; orange only marks focus.
- Claude Code: target version is now 2.1.284, the build it was verified on.
- README: a calm Claude Code session as the hero, a short story of why the palette exists, and a collapsed "See everything at once" section with an editor, a terminal, the full sample render and a color-vision strip. Generated color swatches with what each color is used for, neutral generated badges, and ports grouped by tier with only the supported ones open.
