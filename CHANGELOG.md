# Changelog

## Unreleased

- Foundation: palette source of truth, generator with safe writes, checks (formats, readability, wording, repository hygiene), digest-bound verification tiers, release gate, JSON export.
- Tier changes: Neovim, VS Code, WezTerm, tmux, Starship, Zellij and Claude Code go from experimental to supported, each verified in the real app on macOS 26.6.2.
- tmux: hex colors are now lowercase. tmux expands styles as formats, where `#D` and `#F` are aliases, so uppercase values such as `#D6C9B6` broke the copy-mode selection (it was invisible) and the message and status text colors.
- VS Code: the current find match now has dark text on solid gold, and the other matches keep readable text on their tint. VS Code paints the current match with `editor.findMatchHighlightForeground` and the others with `editor.findMatchForeground`, the reverse of what the names suggest.
- New port: herdr 0.9.1, supported (verified in the real app on macOS 26.6.2). Every theme token is set from palette roles; orange only marks focus.
- Claude Code: target version is now 2.1.284, the build it was verified on.
- README: a calm Claude Code session as the hero, a short story of why the palette exists, and a collapsed "See everything at once" section with an editor, a terminal, the full sample render and a color-vision strip. Generated color swatches with what each color is used for, neutral generated badges, and ports grouped by tier with only the supported ones open.
