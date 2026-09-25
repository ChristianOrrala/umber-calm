-- Umber Calm 0.1.0 — generated from templates/neovim/lua/umber-calm/palette.lua.tmpl. Do not edit. MIT License.
-- Raw colors, role and ANSI slot names, tints in per mille. palette_resolve.lua turns them into hex.
return {
  colors = {
    bg = "#201F1D", bg_dim = "#1A1917", surface = "#2A2826", overlay = "#3C3A36",
    inactive = "#5A554E", dim_text = "#6E6961", muted = "#938A7B", subtle = "#C2A98C",
    text = "#D6C9B6", text_bright = "#EDE3D2", red = "#E08374", orange = "#EDA97C",
    yellow = "#DCC07D", green = "#A7B56E", cyan = "#88C0AE", blue = "#88B0B4", purple = "#C9A0C0",
  },
  ansi = {
    "surface", "red", "green", "yellow",
    "blue", "purple", "cyan", "text",
    "dim_text", "#EC9A8C", "#B9C684", "#E8CE92",
    "#9DC2C5", "#D7B4CF", "#9CCEBC", "text_bright",
  },
  roles = {
    syntax = {
      keyword = "yellow", preproc = "yellow", ["function"] = "blue",
      tag = "blue", type = "cyan", namespace = "cyan",
      attribute = "cyan", string = "green", escape = "purple",
      constant = "purple", builtin = "purple", variable = "text",
      operator = "subtle", comment = "muted", heading = "yellow",
      link = "blue", code = "green",
    },
    ui = {
      bg = "bg", surface = "surface", chrome = "bg_dim",
      selection_bg = "overlay", selection_fg = "text",
      border_strong = "overlay", border = "inactive", text = "text",
      text_secondary = "muted", line_number = "muted",
      line_number_active = "text", text_dim = "dim_text", focus = "orange",
    },
    diag = {
      error = "red", warning = "yellow", info = "blue", hint = "cyan",
      ok = "green", diff_add = "green", diff_delete = "red",
      diff_change = "blue", search = "yellow",
    },
    term = {
      background = "bg", foreground = "text", cursor = "orange",
      cursor_text = "bg", selection_bg = "overlay", selection_fg = "text",
    },
  },
  tints = { diag = 120, diff = 220, search = 180 },
}
