# Style guide

The contracts every port follows. `tests/test_docs.py` checks these tables against `palette/umber-calm.toml`, and `tools/check.py` enforces every pair in the [measured readability](#measured-readability) table below (`readability.PAIRS`).

## Colors

| Name | Hex | Purpose |
|---|---|---|
| `bg` | `#201F1D` | Primary background |
| `bg_dim` | `#1A1917` | Inactive chrome: tab bars, gutters |
| `surface` | `#2A2826` | Panels, status bars, floating windows, sidebars |
| `overlay` | `#3C3A36` | Selection background, strong borders |
| `inactive` | `#5A554E` | Non-text UI only: borders, indent guides, inactive icons (2.2:1, never text) |
| `dim_text` | `#6E6961` | Least important readable text; also ANSI bright black (3.0:1) |
| `muted` | `#938A7B` | Comments, secondary text |
| `subtle` | `#C2A98C` | Operators, punctuation |
| `text` | `#D6C9B6` | Main foreground |
| `text_bright` | `#EDE3D2` | Emphasis only |
| `red` | `#E08374` | Errors, deletions |
| `orange` | `#EDA97C` | Focus |
| `yellow` | `#DCC07D` | Keywords, warnings |
| `green` | `#A7B56E` | Strings, success, additions |
| `cyan` | `#88C0AE` | Types, hints |
| `blue` | `#88B0B4` | Functions, info |
| `purple` | `#C9A0C0` | Constants, numbers |

## Syntax

Templates reference these roles (`syntax.keyword`), never raw color names, so a role change reaches every port (`tests/test_role_propagation.py`).

| Role | Color | Covers |
|---|---|---|
| keyword | `yellow` | `if`, `return`, `import`, storage modifiers |
| preproc | `yellow` | preprocessor directives, decorators, macros |
| function | `blue` | function and method names, definitions and calls |
| tag | `blue` | HTML, JSX and XML tags |
| type | `cyan` | types, classes, interfaces |
| namespace | `cyan` | namespaces and modules |
| attribute | `cyan` | tag attributes |
| string | `green` | strings |
| escape | `purple` | escapes, regular expressions, special strings |
| constant | `purple` | constants, numbers, booleans |
| builtin | `purple` | built-in variables such as `self` and `this` |
| variable | `text` | variables, parameters, properties, fields |
| operator | `subtle` | operators, punctuation, brackets, delimiters |
| comment | `muted` | comments (italic by default); doc-comment tags are bold |
| heading | `yellow` | markup headings (bold) |
| link | `blue` | markup links and URLs (underlined) |
| code | `green` | inline and fenced code in markup |

Deprecated symbols get a strikethrough and keep their color.

**Keyword operators are keywords.** Word operators such as `and`, `or`, `not`, `in`, `is`, `typeof` and `instanceof` (Treesitter `@keyword.operator`) use the keyword color; the operator row covers symbols (`+`, `=>`, `&&`) and punctuation only.

**Readonly bindings are variables.** A `const` or `readonly` binding (LSP `readonly` modifier on a variable) keeps the variable color; the constant color is for literal constants and enum members.

**Red and orange are never syntax colors.** Captures that report a problem inside source text (Treesitter `@comment.error`, `@comment.warning`, `@comment.note`, spelling errors, invalid or illegal scopes) follow the diagnostics contract below and may use red. Every port lists those captures explicitly; everything else it emits for code is a syntax mapping and is checked.

## Interface

| Role | Color | Used for |
|---|---|---|
| bg | `bg` | editor and window background |
| surface | `surface` | panels, status bars, floating windows, sidebars |
| chrome | `bg_dim` | inactive chrome: tab bar background, inactive tabs, gutters |
| selection_bg | `overlay` | selection background |
| selection_fg | `text` | selection foreground, wherever the format supports one |
| border_strong | `overlay` | strong borders, optional current line |
| border | `inactive` | subtle borders, indent guides, inactive icons (never text) |
| text | `text` | primary text |
| text_secondary | `muted` | secondary text |
| line_number | `muted` | line numbers |
| line_number_active | `text` | the current line number |
| text_dim | `dim_text` | least important readable text |
| focus | `orange` | where you are: the cursor, the active tab indicator, the active status segment, the focused pane border |

Focus is never decoration: not for buttons in general, badges, links or syntax. Several widgets may show focus at once when they all point at the same current location.

## Diagnostics and diff

| Role | Color | Background tint over `bg` |
|---|---|---|
| error | `red` | 12 % |
| warning | `yellow` | 12 % |
| info | `blue` | 12 % |
| hint | `cyan` | 12 % |
| ok | `green` | none |
| diff_add | `green` | 22 % (12 % for whole lines in tools that also emphasize changed words) |
| diff_delete | `red` | 22 % (12 %) |
| diff_change | `blue` | 22 % (12 %) |
| search | `yellow` | 18 % for matches; the current match is solid `yellow` with `bg` text |

## Terminal

| Slot | Normal | Bright |
|---|---|---|
| black | `#2A2826` | `#6E6961` |
| red | `#E08374` | `#EC9A8C` |
| green | `#A7B56E` | `#B9C684` |
| yellow | `#DCC07D` | `#E8CE92` |
| blue | `#88B0B4` | `#9DC2C5` |
| magenta | `#C9A0C0` | `#D7B4CF` |
| cyan | `#88C0AE` | `#9CCEBC` |
| white | `#D6C9B6` | `#EDE3D2` |

| Role | Color |
|---|---|
| background | `bg` |
| foreground | `text` |
| cursor | `orange` |
| cursor_text | `bg` |
| selection_bg | `overlay` |
| selection_fg | `text` |

Applications decide how they use ANSI colors, so the terminal contract promises readability, not meaning: every slot except `black` is at least 4.5:1 on `bg`; `bright_black` is 3.0:1 (exception E2); `black` is a background color by design.

## Measured readability

Contrast is the WCAG 2.x ratio. Translucent backgrounds are composited in sRGB channel space over `bg`, rounding half up, exactly as the generator's `blend` does.

| Foreground | on `bg` | on `surface` | Rule |
|---|---|---|---|
| `text` | 10.1 | 9.0 | ≥ 4.5 |
| syntax accents (`yellow` `blue` `cyan` `green` `purple` `subtle`) | 7.0–9.3 | 6.2–8.3 | ≥ 4.5 |
| `red` | 6.0 | 5.4 | ≥ 4.5 |
| `muted` | 4.8 | 4.3 | ≥ 4.5 on `bg`; ≥ 4.0 on `surface` (E1) |
| `dim_text` / ANSI bright black | 3.0 | 2.7 | ≥ 3.0 on `bg` (E2) |
| `orange` | 8.3 | 7.4 | ≥ 3.0 |

| State | Background | `text` on it | `muted` on it |
|---|---|---|---|
| Selection | `overlay` `#3C3A36` | 7.0 | 3.3 |
| Search match | `yellow` 18 % → `#423C2E` | 6.7 | 3.2 |
| Current search match | `yellow`, text `bg` | 9.3 | — |
| Diff added / deleted / changed line | 22 % → `#3E402F` · `#4A3530` · `#373F3E` | 6.5 · 7.0 · 6.6 | 3.1 · 3.3 · 3.2 |
| Diff line, light (12 %) | `#303127` · `#372B27` · `#2C302F` | 8.1 · 8.4 · 8.2 | 3.9 · 4.0 · 3.9 |
| Cursor | `orange`, text `bg` | 8.3 | — |
| Diagnostic virtual text | severity color at 12 % | error 5.0 · warning 7.2 · info 5.7 · hint 6.4 (severity color on its tint) | — |

A port may only blend to a background listed here; `tools/check.py` rejects any other blend.

## Exceptions

- **E1: comments on panels (4.3:1).** Comments are meant to recede; they stay at or above 4.0.
- **E2: ANSI bright black (3.0:1).** Terminal applications use it for de-emphasized text; 3.0 keeps it distinct from `muted` (ΔE_OK 11.5).
- **E3: secondary text on highlights.** Where a format cannot force the foreground to `text` on a highlight (for example VS Code selections), comments may drop to 3.0 on that highlight. Where a format can set a selection foreground, it uses `text`.
