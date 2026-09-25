import unittest
from tests.helpers import load_real_palette, tempdir, write_temp_palette
from umber import filters, palette

P = load_real_palette()

class ColorNameTest(unittest.TestCase):
    def test_name_and_passthrough(self):
        self.assertEqual(filters.apply(P.colors["yellow"], "colorname", [], P), "yellow")
        self.assertEqual(filters.apply(P.ansi["bright_red"], "colorname", [], P), P.ansi["bright_red"])

    def test_ambiguous_value_is_an_error(self):
        with tempdir() as d:
            path = write_temp_palette(d, {f'purple      = "{P.colors["purple"]}"': f'purple      = "{P.colors["blue"]}"'})
            pal = palette.load(path)
            with self.assertRaisesRegex(filters.FilterError, "several colors"):
                filters.apply(pal.colors["blue"], "colorname", [], pal)

if __name__ == "__main__":
    unittest.main()
