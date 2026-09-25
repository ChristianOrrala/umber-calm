import shutil, subprocess, unittest
from pathlib import Path
from tests.helpers import REPO, load_real_palette, tempdir, write_temp_palette
from umber import buildcmd, color, palette, readability, template

P = load_real_palette()
RUNTIME = ["lua/umber-calm/init.lua", "lua/umber-calm/config.lua", "lua/umber-calm/palette_resolve.lua",
           "lua/umber-calm/groups/init.lua", "lua/umber-calm/groups/integrations.lua",
           "lua/lualine/themes/umber-calm.lua", "colors/umber-calm.lua", "doc/umber-calm.txt"]

def setUpModule():
    buildcmd.build(REPO)

class NeovimPort(unittest.TestCase):
    def test_palette_lua_carries_role_names_and_per_mille_tints(self):
        text = (REPO / "lua/umber-calm/palette.lua").read_text(encoding="utf-8")
        for role, name in P.roles["syntax"].items():
            key = '["function"]' if role == "function" else role
            self.assertIn(f'{key} = "{name}"', text)
        for name, amount in P.tints.items():
            self.assertIn(f"{name} = {round(amount * 1000)}", text)
        self.assertEqual(len(set(P.colors.values())), len(P.colors), "colorname needs unique color values")

    def test_tints_follow_the_palette(self):
        """M5: a tint change in the palette reaches the Neovim and JSON outputs (no hard-coded per-mille values)."""
        with tempdir() as d:
            pal = palette.load(write_temp_palette(d, {"diag   = 0.12": "diag   = 0.15", "search = 0.18": "search = 0.2"}))
        for rel, needles in (("templates/neovim/lua/umber-calm/palette.lua.tmpl", ("diag = 150", "diff = 220", "search = 200")),
                             ("templates/json/umber-calm.json.tmpl", ('"diag": 0.15', '"diff": 0.22', '"search": 0.2'))):
            text = template.render((REPO / rel).read_text(encoding="utf-8"), pal, source=rel,
                                   extra={"meta.template": rel})
            for needle in needles:
                self.assertIn(needle, text, rel)

    def test_help_file_has_the_plugin_tag(self):
        doc = (REPO / "doc/umber-calm.txt").read_text(encoding="utf-8")
        self.assertIn("*umber-calm*", doc, ":help umber-calm must resolve")

    def test_every_runtime_file_is_in_the_digest(self):
        inputs = buildcmd.states(REPO)["neovim"].inputs
        for rel in RUNTIME + ["lua/umber-calm/palette.lua", "colors/umber-calm.vim"]:
            self.assertIn(rel, inputs)

    def test_editing_any_runtime_file_expires_the_verification(self):
        with tempdir() as d:
            root = Path(d) / "repo"
            shutil.copytree(REPO, root, ignore=shutil.ignore_patterns(".git", "dist", "__pycache__"))
            before = buildcmd.states(root)["neovim"].digest
            for rel in RUNTIME:
                path = root / rel
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                self.assertNotEqual(buildcmd.states(root)["neovim"].digest, before, rel)
                path.write_bytes(original)
            self.assertEqual(buildcmd.states(root)["neovim"].digest, before)

# Vim core UI groups whose built-in defaults are light, red or off-palette (spec §9 "core UI").
VIM_CORE_UI = ["Normal", "SignColumn", "FoldColumn", "CursorColumn", "ColorColumn", "CursorLine", "CursorLineNr",
               "LineNr", "TabLine", "TabLineFill", "TabLineSel", "WildMenu", "DiffAdd", "DiffChange", "DiffDelete",
               "DiffText", "Folded", "VertSplit", "StatusLine", "StatusLineNC", "StatusLineTerm", "StatusLineTermNC",
               "Pmenu", "PmenuSel", "PmenuSbar", "PmenuThumb", "SpellBad", "SpellCap", "SpellRare", "SpellLocal",
               "ErrorMsg", "WarningMsg", "Question", "MoreMsg", "ModeMsg", "Directory", "Title", "Conceal",
               "NonText", "SpecialKey", "EndOfBuffer", "MatchParen", "Search", "IncSearch", "CurSearch", "Visual",
               "QuickFixLine", "Cursor", "ToolbarLine", "ToolbarButton", "Underlined", "Added", "Changed", "Removed"]
VIM = shutil.which("vim")


def _vim_string(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


@unittest.skipUnless(VIM, "vim is not on PATH")
class VimColorscheme(unittest.TestCase):
    """Runs the generated colors/umber-calm.vim in a real Vim that starts with a light background."""

    def _probe(self) -> tuple[str, dict[str, tuple[str, str]]]:
        with tempdir() as d:
            out = Path(d) / "out.txt"
            script = Path(d) / "probe.vim"
            script.write_text("\n".join([
                "set termguicolors",
                "set background=light",
                f"let &runtimepath = {_vim_string(REPO.as_posix())} . ',' . &runtimepath",
                "colorscheme umber-calm",
                "let s:out = [&background]",
                f"for s:g in {[g for g in VIM_CORE_UI]!r}",
                "  let s:id = synIDtrans(hlID(s:g))",
                "  call add(s:out, s:g . ' ' . synIDattr(s:id, 'fg#') . ' ' . synIDattr(s:id, 'bg#'))",
                "endfor",
                f"call writefile(s:out, {_vim_string(out.as_posix())})",
                "qa!",
            ]) + "\n", encoding="utf-8", newline="\n")
            subprocess.run([VIM, "-Nu", "NONE", "-i", "NONE", "-es", "-S", script.as_posix()],
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
            self.assertTrue(out.is_file(), "vim did not run the probe")
            lines = out.read_text(encoding="utf-8").splitlines()
        groups = {}
        for line in lines[1:]:
            name, fg, bg = (line.split(" ") + ["", ""])[:3]
            groups[name] = (fg.upper(), bg.upper())
        return lines[0], groups

    def test_light_start_ends_dark_with_palette_colors_only(self):
        background, groups = self._probe()
        self.assertEqual(background, "dark")
        allowed = {v.upper() for v in P.colors.values()} | {P.resolve(f"ansi.{s}").upper() for s in P.ansi}
        allowed |= {v.upper() for v in readability.measured_blends(P)}
        for name in VIM_CORE_UI:
            fg, bg = groups[name]
            for value in (fg, bg):
                self.assertTrue(value == "" or value in allowed, f"{name}: {value or 'none'} is not a palette color")

    def test_core_ui_groups_use_their_roles(self):
        _, groups = self._probe()
        r = P.resolve
        expected = {
            "Normal": (r("ui.text"), r("ui.bg")),
            "SignColumn": (r("ui.text_secondary"), r("ui.bg")),
            "ColorColumn": ("", r("ui.surface")),
            "CursorColumn": ("", r("ui.surface")),
            "TabLine": (r("ui.text_secondary"), r("ui.chrome")),
            "DiffText": (r("ui.text"), r("ui.selection_bg")),
            "DiffDelete": (r("ui.text_secondary"), color.blend(r("diag.diff_delete"), r("bg"), P.tints["diff"])),
            "ErrorMsg": (r("diag.error"), ""),
            "Search": (r("ui.text"), color.blend(r("diag.search"), r("bg"), P.tints["search"])),
            "IncSearch": (r("ui.bg"), r("diag.search")),
            "CurSearch": (r("ui.bg"), r("diag.search")),
            "Visual": (r("ui.selection_fg"), r("ui.selection_bg")),
        }
        for name, (fg, bg) in expected.items():
            self.assertEqual(groups[name], (fg.upper(), bg.upper()), name)


if __name__ == "__main__":
    unittest.main()
