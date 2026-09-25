local M = {}

M.defaults = {
  transparent = false,
  terminal_colors = true,
  dim_inactive = false,
  styles = {
    comments = { italic = true },
    keywords = {},
    functions = {},
    variables = {},
    parameters = {},
  },
  integrations = {
    telescope = true,
    gitsigns = true,
    which_key = true,
    lualine = true,
    blink = true,
    cmp = true,
    lazy = true,
    indent_blankline = true,
  },
  on_colors = nil,
  on_highlights = nil,
}

M.options = vim.deepcopy(M.defaults)

function M.setup(opts)
  M.options = vim.tbl_deep_extend("force", vim.deepcopy(M.defaults), opts or {})
end

return M
