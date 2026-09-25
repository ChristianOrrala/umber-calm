import tomllib, unittest
from tests.helpers import PALETTE_PATH, load_real_palette, write_temp_palette, tempdir
from umber import palette


def file_release() -> str:
    """The release written in the palette file, read independently of the loader (never a hard-coded version)."""
    return tomllib.loads(PALETTE_PATH.read_text(encoding="utf-8"))["meta"]["release"]

class PaletteTest(unittest.TestCase):
    def test_resolves_every_namespace(self):
        p = load_real_palette()
        self.assertEqual(p.resolve("blue"), "#88B0B4")
        self.assertEqual(p.resolve("syntax.keyword"), "#DCC07D")
        self.assertEqual(p.resolve("ui.focus"), "#EDA97C")
        self.assertEqual(p.resolve("diag.error"), "#E08374")
        self.assertEqual(p.resolve("term.cursor_text"), "#201F1D")
        self.assertEqual(p.resolve("ansi.bright_black"), "#6E6961")
        self.assertEqual(p.resolve("ansi.bright_red"), "#EC9A8C")
        self.assertEqual(p.resolve("meta.slug"), "umber-calm")
        self.assertRegex(file_release(), r"\A[0-9]+\.[0-9]+\.[0-9]+\Z")
        self.assertEqual(p.resolve("meta.release"), file_release())
        self.assertEqual(p.tint("tint.search"), 0.18)
        self.assertEqual(p.tint("0.5"), 0.5)
        self.assertTrue(p.is_color_value("ui.focus"))
        self.assertFalse(p.is_color_value("meta.slug"))
        self.assertFalse(p.is_color_value("nope"))

    def test_unknown_reference(self):
        p = load_real_palette()
        for ref in ("nope", "syntax.nope", "ansi.orange", "meta.nope", "role.keyword"):
            with self.assertRaises(palette.PaletteError):
                p.resolve(ref)

    def test_rejects_red_or_orange_in_syntax(self):
        for color_name in ("red", "orange"):
            with tempdir() as d:
                path = write_temp_palette(d, {'keyword   = "yellow"': f'keyword   = "{color_name}"'})
                with self.assertRaisesRegex(palette.PaletteError, "reserved"):
                    palette.load(path)

    def test_rejects_invalid_hex_including_trailing_newline(self):
        for bad in ('"#201F1"', '"#201F1D\\n"'):
            with tempdir() as d:
                path = write_temp_palette(d, {'bg          = "#201F1D"': f'bg          = {bad}'})
                with self.assertRaisesRegex(palette.PaletteError, "bg"):
                    palette.load(path)

    def test_rejects_missing_ansi_slot(self):
        with tempdir() as d:
            path = write_temp_palette(d, {'bright_cyan    = "#9CCEBC"\n': ""})
            with self.assertRaisesRegex(palette.PaletteError, "bright_cyan"):
                palette.load(path)

    def test_rejects_role_pointing_to_unknown_color(self):
        with tempdir() as d:
            path = write_temp_palette(d, {'focus              = "orange"': 'focus              = "amber"'})
            with self.assertRaisesRegex(palette.PaletteError, "amber"):
                palette.load(path)

    def test_rejects_missing_required_role(self):
        with tempdir() as d:
            path = write_temp_palette(d, {'comment   = "muted"\n': ""})
            with self.assertRaisesRegex(palette.PaletteError, "comment"):
                palette.load(path)

    def test_validates_meta_types(self):
        cases = {'schema_version = 1': 'schema_version = "1"',
                 f'release = "{file_release()}"': 'release = "0.1"',
                 'homepage = "https://github.com/ChristianOrrala/umber-calm"': 'homepage = "http://x"'}
        for old, new in cases.items():
            with tempdir() as d:
                path = write_temp_palette(d, {old: new})
                with self.assertRaises(palette.PaletteError, msg=new):
                    palette.load(path)

    def test_tints_need_at_most_three_decimals(self):
        with tempdir() as d:
            path = write_temp_palette(d, {"search = 0.18": "search = 0.1875"})
            with self.assertRaisesRegex(palette.PaletteError, "three decimals"):
                palette.load(path)

if __name__ == "__main__":
    unittest.main()
