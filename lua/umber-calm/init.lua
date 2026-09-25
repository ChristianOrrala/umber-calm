local config = require("umber-calm.config")

local M = {}
local cache

--- Merge options. Call before or after :colorscheme; after, it re-applies the active scheme through
--- :colorscheme, so ColorScheme listeners (lualine and others) rebuild with the new colors.
function M.setup(opts)
  config.setup(opts)
  cache = nil
  if vim.g.colors_name == "umber-calm" then
    vim.cmd.colorscheme("umber-calm")
  end
end

--- The resolved palette: raw colors (after on_colors), roles, ANSI, tints — all hex.
function M.resolved()
  if not cache then
    local spec = require("umber-calm.palette")
    local colors = vim.deepcopy(spec.colors)
    if config.options.on_colors then
      config.options.on_colors(colors)
    end
    cache = require("umber-calm.palette_resolve").resolve(colors, spec)
  end
  return cache
end

M.colors = M.resolved

function M.load()
  vim.cmd("hi clear")
  if vim.fn.exists("syntax_on") == 1 then
    vim.cmd("syntax reset")
  end
  vim.o.termguicolors = true
  vim.o.background = "dark"
  vim.g.colors_name = "umber-calm"
  cache = nil
  local c = M.resolved()
  local hl = require("umber-calm.groups").build(c, config.options)
  if config.options.on_highlights then
    config.options.on_highlights(hl, c)
  end
  for group, spec in pairs(hl) do
    vim.api.nvim_set_hl(0, group, spec)
  end
  for i = 0, 15 do
    vim.g["terminal_color_" .. i] = config.options.terminal_colors and c.ansi[i + 1] or nil
  end
  package.loaded["lualine.themes.umber-calm"] = nil
end

return M
