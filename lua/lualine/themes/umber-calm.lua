-- lualine theme for Umber Calm. Follows on_colors through require("umber-calm").resolved().
local config = require("umber-calm.config")
if not config.options.integrations.lualine then
  return require("lualine.themes.auto")
end

local c = require("umber-calm").resolved()
local u = c.ui

-- The active mode segment marks where you are, so it is focus in every mode; the mode name tells them apart.
local function mode()
  return {
    a = { fg = u.bg, bg = u.focus, gui = "bold" },
    b = { fg = u.text, bg = u.border_strong },
    c = { fg = u.text_secondary, bg = u.surface },
  }
end

return {
  normal = mode(),
  insert = mode(),
  visual = mode(),
  replace = mode(),
  command = mode(),
  inactive = {
    a = { fg = u.text_secondary, bg = u.chrome },
    b = { fg = u.text_secondary, bg = u.chrome },
    c = { fg = u.text_secondary, bg = u.chrome },
  },
}
