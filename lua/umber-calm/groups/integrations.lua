local M = {}

--- Add plugin groups for every enabled integration (lualine is handled by its theme file).
function M.apply(hl, c, i)
  local s, u, d = c.syntax, c.ui, c.diag
  if i.telescope then
    hl.TelescopeNormal = { fg = u.text, bg = u.surface }
    hl.TelescopeBorder = { fg = u.border_strong, bg = u.surface }
    hl.TelescopePromptNormal = { fg = u.text, bg = u.surface }
    hl.TelescopePromptBorder = { fg = u.border_strong, bg = u.surface }
    hl.TelescopePromptPrefix = { fg = u.focus, bg = u.surface }
    hl.TelescopeTitle = { fg = u.text, bold = true }
    hl.TelescopeSelection = { fg = u.selection_fg, bg = u.selection_bg }
    hl.TelescopeSelectionCaret = { fg = u.focus, bg = u.selection_bg }
    hl.TelescopeMatching = { fg = d.search, bold = true }
  end
  if i.gitsigns then
    hl.GitSignsAdd = { fg = d.diff_add }
    hl.GitSignsChange = { fg = d.diff_change }
    hl.GitSignsDelete = { fg = d.diff_delete }
    hl.GitSignsChangedelete = { fg = d.diff_change }
    hl.GitSignsUntracked = { fg = d.ok }
  end
  if i.which_key then
    hl.WhichKey = { fg = s["function"] }
    hl.WhichKeyGroup = { fg = s.keyword }
    hl.WhichKeyDesc = { fg = u.text }
    hl.WhichKeySeparator = { fg = u.text_secondary }
    hl.WhichKeyValue = { fg = u.text_secondary }
    hl.WhichKeyNormal = { bg = u.surface }
    hl.WhichKeyBorder = { fg = u.border_strong, bg = u.surface }
  end
  if i.blink then
    hl.BlinkCmpMenu = { fg = u.text, bg = u.surface }
    hl.BlinkCmpMenuBorder = { fg = u.border_strong, bg = u.surface }
    hl.BlinkCmpMenuSelection = { bg = u.selection_bg }
    hl.BlinkCmpLabel = { fg = u.text }
    hl.BlinkCmpLabelMatch = { fg = d.search, bold = true }
    hl.BlinkCmpLabelDeprecated = { fg = u.text_secondary, strikethrough = true }
    hl.BlinkCmpKind = { fg = s.type }
    hl.BlinkCmpDoc = { fg = u.text, bg = u.surface }
    hl.BlinkCmpDocBorder = { fg = u.border_strong, bg = u.surface }
    hl.BlinkCmpSignatureHelp = { fg = u.text, bg = u.surface }
    hl.BlinkCmpGhostText = { fg = u.text_dim }
  end
  if i.cmp then
    hl.CmpItemAbbr = { fg = u.text }
    hl.CmpItemAbbrMatch = { fg = d.search, bold = true }
    hl.CmpItemAbbrMatchFuzzy = { fg = d.search, bold = true }
    hl.CmpItemAbbrDeprecated = { fg = u.text_secondary, strikethrough = true }
    hl.CmpItemKind = { fg = s.type }
    hl.CmpItemMenu = { fg = u.text_secondary }
  end
  if i.lazy then
    hl.LazyNormal = { fg = u.text, bg = u.surface }
    hl.LazyButton = { fg = u.text, bg = u.border_strong }
    hl.LazyButtonActive = { fg = u.text, bg = u.selection_bg, bold = true }
    hl.LazyH1 = { fg = u.bg, bg = s["function"], bold = true }
    hl.LazyH2 = { fg = s.heading, bold = true }
    hl.LazyComment = { fg = s.comment }
    hl.LazyProgressDone = { fg = d.ok }
    hl.LazyProgressTodo = { fg = u.border }
    hl.LazySpecial = { fg = s.escape }
  end
  if i.indent_blankline then
    hl.IblIndent = { fg = u.border } -- indent guides are subtle non-text chrome
    hl.IblScope = { fg = u.text_secondary } -- the current scope, one step brighter than the guides
    hl.IblWhitespace = { fg = u.border }
  end
end

return M
