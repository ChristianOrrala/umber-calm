-- Headless coverage matrix for the Neovim plugin (spec §9).
-- Run from the repository root: nvim --headless --clean -l tests/nvim/run.lua
local root = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":p:h:h:h")
vim.opt.rtp:prepend(root)

local failures = 0
local function check(name, cond, detail)
  if cond then
    io.stdout:write("ok   " .. name .. "\n")
  else
    failures = failures + 1
    io.stderr:write("FAIL " .. name .. (detail and (": " .. tostring(detail)) or "") .. "\n")
  end
end

local function hex(n)
  return n and string.format("#%06X", n) or nil
end

local function get(group)
  local h = vim.api.nvim_get_hl(0, { name = group, link = false })
  return { fg = hex(h.fg), bg = hex(h.bg), italic = h.italic, raw = h }
end

local function exists(group)
  return next(vim.api.nvim_get_hl(0, { name = group })) ~= nil
end

local umber = require("umber-calm")
local resolve = require("umber-calm.palette_resolve")
local groups = require("umber-calm.groups")

local function with(opts, fn)
  umber.setup(opts)
  vim.cmd.colorscheme("umber-calm")
  fn(umber.resolved())
  umber.setup({})
  vim.cmd.colorscheme("umber-calm")
end

-- 1. Loads, names itself, core groups.
vim.cmd.colorscheme("umber-calm")
local R = umber.resolved()
check("colors_name", vim.g.colors_name == "umber-calm")
check("Normal", get("Normal").fg == R.ui.text and get("Normal").bg == R.ui.bg, vim.inspect(get("Normal")))
check("CursorLineNr", get("CursorLineNr").fg == R.ui.line_number_active)
check("Visual has selection fg", get("Visual").fg == R.ui.selection_fg and get("Visual").bg == R.ui.selection_bg)
check("terminal_color_8", vim.g.terminal_color_8 == R.ansi[9])

-- 2. Every role reaches its key group.
local expected = {
  Statement = "keyword",
  PreProc = "preproc",
  Function = "function",
  ["@tag"] = "tag",
  Type = "type",
  ["@module"] = "namespace",
  ["@tag.attribute"] = "attribute",
  String = "string",
  ["@string.escape"] = "escape",
  Constant = "constant",
  ["@variable.builtin"] = "builtin",
  ["@variable"] = "variable",
  Operator = "operator",
  Comment = "comment",
  ["@markup.heading"] = "heading",
  ["@markup.link"] = "link",
  ["@markup.raw"] = "code",
}
for group, role in pairs(expected) do
  check("role " .. role .. " -> " .. group, get(group).fg == R.syntax[role], get(group).fg)
end

-- 3. Every emitted syntax group exists and is never red or orange.
local emitted = groups.build(R, require("umber-calm.config").options)
local syntax = {}
for _, g in ipairs(groups.legacy_syntax) do
  syntax[g] = true
end
for g in pairs(emitted) do
  if g:sub(1, 1) == "@" then
    syntax[g] = true
  end
end
local reserved = { [R.colors.red] = "red", [R.colors.orange] = "orange" }
local count = 0
for g in pairs(syntax) do
  if not groups.diagnostic_captures[g] then
    count = count + 1
    check("syntax exists: " .. g, exists(g))
    local fg = get(g).fg
    check("syntax not reserved: " .. g, fg == nil or reserved[fg] == nil, fg and reserved[fg])
  end
end
check("syntax groups checked", count > 80, count)
check(
  "@lsp.type.variable links to @variable",
  vim.api.nvim_get_hl(0, { name = "@lsp.type.variable" }).link == "@variable"
)
-- A TypeScript `const` binding is a readonly variable, not a constant: it stays text.
check(
  "@lsp.typemod.variable.readonly links to @variable",
  vim.api.nvim_get_hl(0, { name = "@lsp.typemod.variable.readonly" }).link == "@variable"
)
check("@markup.link is underlined", get("@markup.link").raw.underline == true)
check("@markup.link.url is underlined", get("@markup.link.url").raw.underline == true)
-- Indent guides are subtle non-text chrome (ui.border); the current scope is a step brighter.
check("IblIndent uses ui.border", get("IblIndent").fg == R.ui.border, get("IblIndent").fg)
check("IblWhitespace uses ui.border", get("IblWhitespace").fg == R.ui.border, get("IblWhitespace").fg)
check("IblScope is distinct from the guides", get("IblScope").fg ~= R.ui.border, get("IblScope").fg)

-- lualine: the active mode segment is focus in every mode (the mode name tells the modes apart); b and c neutral.
local lualine = require("lualine.themes.umber-calm")
for _, m in ipairs({ "normal", "insert", "visual", "replace", "command" }) do
  check("lualine " .. m .. ".a is focus", lualine[m].a.bg == R.ui.focus and lualine[m].a.fg == R.ui.bg, lualine[m].a.bg)
  check("lualine " .. m .. ".b neutral", lualine[m].b.bg == R.ui.border_strong and lualine[m].b.fg == R.ui.text)
  check("lualine " .. m .. ".c neutral", lualine[m].c.bg == R.ui.surface and lualine[m].c.fg == R.ui.text_secondary)
end

-- 4. Diagnostics and LSP.
for _, sev in ipairs({ "Error", "Warn", "Info", "Hint" }) do
  local role = ({ Error = "error", Warn = "warning", Info = "info", Hint = "hint" })[sev]
  for _, kind in ipairs({ "", "Sign", "Floating" }) do
    check("Diagnostic" .. kind .. sev, get("Diagnostic" .. kind .. sev).fg == R.diag[role])
  end
  local vt = get("DiagnosticVirtualText" .. sev)
  check("DiagnosticVirtualText" .. sev, vt.fg == R.diag[role] and vt.bg == R.tinted[role], vim.inspect(vt))
  check("DiagnosticUnderline" .. sev, get("DiagnosticUnderline" .. sev).raw.undercurl == true)
end
check("DiagnosticDeprecated", get("DiagnosticDeprecated").raw.strikethrough == true)
check("DiagnosticUnnecessary", get("DiagnosticUnnecessary").fg == R.ui.text_secondary)
check("DiagnosticOk", get("DiagnosticOk").fg == R.diag.ok)
check("Search tint", get("Search").bg == R.tinted.search and get("Search").fg == R.ui.text)
check("CurSearch", get("CurSearch").bg == R.diag.search and get("CurSearch").fg == R.ui.bg)
check("DiffAdd tint", get("DiffAdd").bg == R.tinted.diff_add)

-- 5. Lua blends match the Python generator exactly.
local py = vim.fn.system({ "python3", root .. "/tests/nvim/blend_expect.py" })
local ok, want = pcall(vim.json.decode, py)
check("python expectations", ok, py)
if ok then
  for name, value in pairs(want) do
    if name ~= "boundary" then
      check("blend " .. name, R.tinted[name] == value, R.tinted[name] .. " vs " .. value)
    end
  end
  check("blend boundary", resolve.blend("#000000", "#050505", 900) == want.boundary)
end

-- 6. Idempotent, and switching away and back restores the full state.
local dump = vim.api.nvim_get_hl(0, {})
vim.cmd.colorscheme("umber-calm")
check("idempotent", vim.deep_equal(dump, vim.api.nvim_get_hl(0, {})))
vim.cmd.colorscheme("default")
check("default replaced it", get("Normal").bg ~= R.ui.bg)
vim.cmd.colorscheme("umber-calm")
check("switch back restores every group", vim.deep_equal(dump, vim.api.nvim_get_hl(0, {})))
check("switch back restores terminal colors", vim.g.terminal_color_0 == R.ansi[1])

-- 7. Options, one test each.
with({ transparent = true }, function()
  check("transparent", get("Normal").bg == nil, get("Normal").bg)
end)
with({ dim_inactive = true }, function(c)
  check("dim_inactive", get("NormalNC").bg == c.ui.chrome, get("NormalNC").bg)
end)
with({ terminal_colors = false }, function()
  check("terminal_colors = false", vim.g.terminal_color_0 == nil and vim.g.terminal_color_15 == nil)
end)
with({ styles = { keywords = { italic = true }, comments = { italic = false } } }, function()
  check("styles.keywords", get("Statement").italic == true)
  check("styles.comments", not get("Comment").italic)
end)
with({
  on_highlights = function(hl, c)
    hl.Comment = { fg = c.colors.text }
  end,
}, function(c)
  check("on_highlights wins", get("Comment").fg == c.colors.text)
end)
with({
  on_colors = function(colors)
    colors.blue = "#123456"
    colors.orange = "#654321"
  end,
}, function(c)
  check("on_colors: role follows", get("Function").fg == "#123456", get("Function").fg)
  check("on_colors: tint follows", get("DiagnosticVirtualTextInfo").bg == resolve.blend("#123456", c.colors.bg, 120))
  local theme = require("lualine.themes.umber-calm")
  check("on_colors: lualine follows", theme.normal.a.bg == "#654321", theme.normal.a.bg)
end)

local samples = {
  telescope = "TelescopeNormal",
  gitsigns = "GitSignsAdd",
  which_key = "WhichKey",
  blink = "BlinkCmpMenu",
  cmp = "CmpItemAbbr",
  lazy = "LazyNormal",
  indent_blankline = "IblIndent",
}
for name, group in pairs(samples) do
  check("integration on: " .. name, exists(group))
  with({ integrations = { [name] = false } }, function()
    check("integration off: " .. name, not exists(group))
  end)
end
package.preload["lualine.themes.auto"] = function()
  return { auto = true }
end
with({ integrations = { lualine = false } }, function()
  check("integration off: lualine", require("lualine.themes.umber-calm").auto == true)
end)
check("integration on: lualine", require("lualine.themes.umber-calm").normal ~= nil)

-- setup() after :colorscheme re-applies through :colorscheme, so ColorScheme listeners (lualine) see it.
vim.cmd.colorscheme("umber-calm")
local fired = 0
local listener = vim.api.nvim_create_autocmd("ColorScheme", {
  callback = function()
    fired = fired + 1
  end,
})
umber.setup({
  on_colors = function(colors)
    colors.blue = "#123456"
    colors.orange = "#654321"
  end,
})
check("setup after colorscheme fires ColorScheme", fired == 1, fired)
check("setup after colorscheme: Function follows", get("Function").fg == "#123456", get("Function").fg)
local after = require("lualine.themes.umber-calm")
check("setup after colorscheme: lualine follows", after.normal.a.bg == "#654321", after.normal.a.bg)
vim.api.nvim_del_autocmd(listener)
umber.setup({})
check("setup({}) after colorscheme restores every group", vim.deep_equal(dump, vim.api.nvim_get_hl(0, {})))

-- 8. A role change in the palette reaches every group that uses it.
local spec = vim.deepcopy(require("umber-calm.palette"))
spec.roles.syntax.keyword = "purple"
local mutated = groups.build(resolve.resolve(vim.deepcopy(spec.colors), spec), require("umber-calm.config").options)
check("role mutation", mutated.Statement.fg == R.colors.purple, mutated.Statement.fg)

if failures > 0 then
  io.stderr:write(failures .. " failure(s)\n")
  os.exit(1)
end
print("all neovim checks passed")
