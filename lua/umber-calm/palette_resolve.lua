-- Turns the generated palette (color names, per-mille tints) into hex. See :help umber-calm-colors.
local M = {}

local function channels(hex)
  return tonumber(hex:sub(2, 3), 16), tonumber(hex:sub(4, 5), 16), tonumber(hex:sub(6, 7), 16)
end

--- Blend `fg` over `bg` by `t` per mille (0..1000).
--- Integer math: (t*x + (1000-t)*y + 500) // 1000, identical to tools/umber/color.py.
function M.blend(fg, bg, t)
  local fr, fgg, fb = channels(fg)
  local br, bgg, bb = channels(bg)
  local function mix(x, y)
    return math.floor((t * x + (1000 - t) * y + 500) / 1000)
  end
  return string.format("#%02X%02X%02X", mix(fr, br), mix(fgg, bgg), mix(fb, bb))
end

local function hex(colors, value)
  local found = value:sub(1, 1) == "#" and value or colors[value]
  if type(found) ~= "string" or not found:match("^#%x%x%x%x%x%x$") then
    error("umber-calm: color '" .. tostring(value) .. "' is missing or not #RRGGBB", 0)
  end
  return found:upper()
end

--- Resolve roles, ANSI slots and tints against `colors` (the raw colors after on_colors).
function M.resolve(colors, spec)
  local r = { colors = {}, ansi = {}, syntax = {}, ui = {}, diag = {}, term = {} }
  for name in pairs(spec.colors) do
    r.colors[name] = hex(colors, name)
  end
  for i, name in ipairs(spec.ansi) do
    r.ansi[i] = hex(colors, name)
  end
  for _, contract in ipairs({ "syntax", "ui", "diag", "term" }) do
    for role, name in pairs(spec.roles[contract]) do
      r[contract][role] = hex(colors, name)
    end
  end
  local bg, d, t = r.colors.bg, r.diag, spec.tints
  r.tinted = {
    search = M.blend(d.search, bg, t.search),
    diff_add = M.blend(d.diff_add, bg, t.diff),
    diff_delete = M.blend(d.diff_delete, bg, t.diff),
    diff_change = M.blend(d.diff_change, bg, t.diff),
    error = M.blend(d.error, bg, t.diag),
    warning = M.blend(d.warning, bg, t.diag),
    info = M.blend(d.info, bg, t.diag),
    hint = M.blend(d.hint, bg, t.diag),
  }
  return r
end

return M
