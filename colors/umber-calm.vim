" Umber Calm 0.1.0 — generated from templates/vim/colors/umber-calm.vim.tmpl. Do not edit. MIT License.
" Neovim finds this file before colors/umber-calm.lua: hand over to the Lua plugin.
if has('nvim')
  lua require('umber-calm').load()
  finish
endif
" 'background' first: :hi clear restores the defaults of the current background.
set background=dark
hi clear
if exists("syntax_on") | syntax reset | endif
let g:colors_name = "umber-calm"
" Core UI: every group whose Vim default is light, red or outside the palette is set in full.
hi Normal guifg=#D6C9B6 guibg=#201F1D gui=NONE ctermfg=187 ctermbg=234 cterm=NONE
hi CursorLine guifg=NONE guibg=#2A2826 gui=NONE ctermfg=NONE ctermbg=235 cterm=NONE
hi CursorColumn guifg=NONE guibg=#2A2826 gui=NONE ctermfg=NONE ctermbg=235 cterm=NONE
hi ColorColumn guifg=NONE guibg=#2A2826 gui=NONE ctermfg=NONE ctermbg=235 cterm=NONE
hi CursorLineNr guifg=#D6C9B6 guibg=NONE gui=bold ctermfg=187 ctermbg=NONE cterm=bold
hi LineNr guifg=#938A7B guibg=NONE gui=NONE ctermfg=102 ctermbg=NONE cterm=NONE
hi SignColumn guifg=#938A7B guibg=#201F1D gui=NONE ctermfg=102 ctermbg=234 cterm=NONE
hi FoldColumn guifg=#6E6961 guibg=#201F1D gui=NONE ctermfg=242 ctermbg=234 cterm=NONE
hi Folded guifg=#938A7B guibg=#2A2826 gui=NONE ctermfg=102 ctermbg=235 cterm=NONE
hi Visual guifg=#D6C9B6 guibg=#3C3A36 gui=NONE ctermfg=187 ctermbg=237 cterm=NONE
hi Search guifg=#D6C9B6 guibg=#423C2E gui=NONE ctermfg=187 ctermbg=237 cterm=NONE
hi IncSearch guifg=#201F1D guibg=#DCC07D gui=NONE ctermfg=234 ctermbg=180 cterm=NONE
hi QuickFixLine guifg=NONE guibg=#3C3A36 gui=NONE ctermfg=NONE ctermbg=237 cterm=NONE
hi MatchParen guifg=#D6C9B6 guibg=#3C3A36 gui=bold ctermfg=187 ctermbg=237 cterm=bold
hi Cursor guifg=#201F1D guibg=#EDA97C gui=NONE ctermfg=234 ctermbg=216 cterm=NONE
hi StatusLine guifg=#D6C9B6 guibg=#2A2826 gui=NONE ctermfg=187 ctermbg=235 cterm=NONE
hi StatusLineNC guifg=#938A7B guibg=#1A1917 gui=NONE ctermfg=102 ctermbg=234 cterm=NONE
hi VertSplit guifg=#5A554E guibg=#201F1D gui=NONE ctermfg=240 ctermbg=234 cterm=NONE
hi TabLine guifg=#938A7B guibg=#1A1917 gui=NONE ctermfg=102 ctermbg=234 cterm=NONE
hi TabLineFill guifg=NONE guibg=#1A1917 gui=NONE ctermfg=NONE ctermbg=234 cterm=NONE
hi TabLineSel guifg=#D6C9B6 guibg=#201F1D gui=bold ctermfg=187 ctermbg=234 cterm=bold
hi WildMenu guifg=#D6C9B6 guibg=#3C3A36 gui=bold ctermfg=187 ctermbg=237 cterm=bold
hi Pmenu guifg=#D6C9B6 guibg=#2A2826 gui=NONE ctermfg=187 ctermbg=235 cterm=NONE
hi PmenuSel guifg=#D6C9B6 guibg=#3C3A36 gui=NONE ctermfg=187 ctermbg=237 cterm=NONE
hi PmenuSbar guifg=NONE guibg=#2A2826 gui=NONE ctermfg=NONE ctermbg=235 cterm=NONE
hi PmenuThumb guifg=NONE guibg=#5A554E gui=NONE ctermfg=NONE ctermbg=240 cterm=NONE
hi ToolbarLine guifg=NONE guibg=#2A2826 gui=NONE ctermfg=NONE ctermbg=235 cterm=NONE
hi ToolbarButton guifg=#D6C9B6 guibg=#3C3A36 gui=bold ctermfg=187 ctermbg=237 cterm=bold
hi NonText guifg=#5A554E guibg=NONE gui=NONE ctermfg=240 ctermbg=NONE cterm=NONE
hi SpecialKey guifg=#5A554E guibg=NONE gui=NONE ctermfg=240 ctermbg=NONE cterm=NONE
hi Conceal guifg=#938A7B guibg=NONE gui=NONE ctermfg=102 ctermbg=NONE cterm=NONE
hi Directory guifg=#88B0B4 guibg=NONE gui=NONE ctermfg=109 ctermbg=NONE cterm=NONE
hi Title guifg=#DCC07D guibg=NONE gui=bold ctermfg=180 ctermbg=NONE cterm=bold
hi ErrorMsg guifg=#E08374 guibg=NONE gui=NONE ctermfg=174 ctermbg=NONE cterm=NONE
hi WarningMsg guifg=#DCC07D guibg=NONE gui=NONE ctermfg=180 ctermbg=NONE cterm=NONE
hi Question guifg=#88B0B4 guibg=NONE gui=NONE ctermfg=109 ctermbg=NONE cterm=NONE
hi MoreMsg guifg=#A7B56E guibg=NONE gui=NONE ctermfg=143 ctermbg=NONE cterm=NONE
hi ModeMsg guifg=#D6C9B6 guibg=NONE gui=bold ctermfg=187 ctermbg=NONE cterm=bold
hi DiffAdd guifg=NONE guibg=#3E402F gui=NONE ctermfg=NONE ctermbg=237 cterm=NONE
hi DiffChange guifg=NONE guibg=#373F3E gui=NONE ctermfg=NONE ctermbg=237 cterm=NONE
hi DiffDelete guifg=#938A7B guibg=#4A3530 gui=NONE ctermfg=102 ctermbg=237 cterm=NONE
hi DiffText guifg=#D6C9B6 guibg=#3C3A36 gui=bold ctermfg=187 ctermbg=237 cterm=bold
hi Added guifg=#A7B56E guibg=NONE gui=NONE ctermfg=143 ctermbg=NONE cterm=NONE
hi Changed guifg=#88B0B4 guibg=NONE gui=NONE ctermfg=109 ctermbg=NONE cterm=NONE
hi Removed guifg=#E08374 guibg=NONE gui=NONE ctermfg=174 ctermbg=NONE cterm=NONE
hi! link VisualNOS Visual
hi! link CurSearch IncSearch
hi! link lCursor Cursor
hi! link CursorIM Cursor
hi! link StatusLineTerm StatusLine
hi! link StatusLineTermNC StatusLineNC
hi SpellBad guifg=NONE guibg=NONE guisp=#E08374 gui=undercurl ctermfg=NONE ctermbg=NONE cterm=underline
hi SpellCap guifg=NONE guibg=NONE guisp=#DCC07D gui=undercurl ctermfg=NONE ctermbg=NONE cterm=underline
hi SpellLocal guifg=NONE guibg=NONE guisp=#88B0B4 gui=undercurl ctermfg=NONE ctermbg=NONE cterm=underline
hi SpellRare guifg=NONE guibg=NONE guisp=#88C0AE gui=undercurl ctermfg=NONE ctermbg=NONE cterm=underline
hi Comment guifg=#938A7B ctermfg=102 gui=italic cterm=italic
hi Constant guifg=#C9A0C0 ctermfg=181
hi String guifg=#A7B56E ctermfg=143
hi Identifier guifg=#D6C9B6 ctermfg=187 gui=NONE cterm=NONE
hi Function guifg=#88B0B4 ctermfg=109
hi Statement guifg=#DCC07D ctermfg=180 gui=NONE cterm=NONE
hi Operator guifg=#C2A98C ctermfg=144
hi PreProc guifg=#DCC07D ctermfg=180
hi Type guifg=#88C0AE ctermfg=109 gui=NONE cterm=NONE
hi Special guifg=#C9A0C0 ctermfg=181
hi Tag guifg=#88B0B4 ctermfg=109
hi Delimiter guifg=#C2A98C ctermfg=144
hi Title guifg=#DCC07D ctermfg=180 gui=bold cterm=bold
hi Directory guifg=#88B0B4 ctermfg=109
hi Error guifg=#E08374 guibg=NONE ctermfg=174 ctermbg=NONE
hi Todo guifg=#201F1D guibg=#DCC07D ctermfg=234 ctermbg=180 gui=bold cterm=bold
hi Underlined guifg=#88B0B4 ctermfg=109 gui=underline cterm=underline
hi link Character String
hi link Number Constant
hi link Boolean Constant
hi link Float Constant
hi link Conditional Statement
hi link Repeat Statement
hi link Label Statement
hi link Keyword Statement
hi link Exception Statement
hi link Include PreProc
hi link Define PreProc
hi link Macro PreProc
hi link StorageClass Statement
hi link Structure Type
hi link Typedef Type
hi link SpecialChar Special
