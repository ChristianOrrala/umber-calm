# Neovim — Umber Calm

Tier: 🧪 experimental

Target version: 0.10 · Format documentation: https://neovim.io/doc/user/syntax.html#highlight-groups

Verified on: —

## Install

lazy.nvim: `{ "ChristianOrrala/umber-calm", lazy = false, priority = 1000, config = function() vim.cmd.colorscheme("umber-calm") end }`. Optional: `require("umber-calm").setup({ ... })` before the colorscheme call (see :help umber-calm).

## Uninstall

Remove the plugin spec and choose another colorscheme.

## Verification checklist

- [ ] Normal, CursorLine, Visual (text stays readable), Search/CurSearch
- [ ] Treesitter: keywords gold, functions teal-slate, types sea-green, strings olive, constants mauve, operators tan, comments muted italic
- [ ] diagnostics with tinted virtual text
- [ ] telescope, gitsigns, which-key, blink.cmp/nvim-cmp, lazy UI, indent-blankline
- [ ] lualine theme: the mode segment is orange (focus) in every mode
- [ ] :terminal colors
- [ ] :help umber-calm opens

## Verification

Current digest: `sha256:8b91eb053607927fd4499a62189e314e596f92979cd2dadf0c0c69323aeb6751`

Print it yourself with `python3 tools/build.py digest neovim`. It covers these files:

- `colors/umber-calm.lua`
- `colors/umber-calm.vim`
- `doc/umber-calm.txt`
- `lua/lualine/themes/umber-calm.lua`
- `lua/umber-calm/config.lua`
- `lua/umber-calm/groups/init.lua`
- `lua/umber-calm/groups/integrations.lua`
- `lua/umber-calm/init.lua`
- `lua/umber-calm/palette.lua`
- `lua/umber-calm/palette_resolve.lua`

No verification recorded yet.

Generated from ports.toml and verifications.json — do not edit. MIT License — see the repository LICENSE.
