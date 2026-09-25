import unittest
from tests.helpers import load_real_palette
from umber import filters

P = load_real_palette()
f = lambda v, name, *args: filters.apply(v, name, list(args), P)

class FiltersTest(unittest.TestCase):
    def test_simple_formats(self):
        self.assertEqual(f("#88B0B4", "lower"), "#88b0b4")
        self.assertEqual(f("#88B0B4", "nohash"), "88B0B4")
        self.assertEqual(f("#88B0B4", "rgb_decimal"), "136,176,180")
        self.assertEqual(f("#88B0B4", "ansi256"), "109")

    def test_alpha_variants(self):
        self.assertEqual(f("#88B0B4", "alpha", "4d"), "#88B0B44D")
        self.assertEqual(f("#88B0B4", "rgba_nohash", "FF"), "88B0B4FF")
        self.assertEqual(f("#88B0B4", "argb", "FF"), "#FF88B0B4")

    def test_channel(self):
        self.assertEqual(f("#88B0B4", "channel", "r"), "0.533333")
        self.assertEqual(f("#88B0B4", "channel", "b"), "0.705882")

    def test_blend(self):
        self.assertEqual(f("#DCC07D", "blend", "bg", "tint.search"), "#423C2E")
        self.assertEqual(f("#DCC07D", "blend", "bg", "0.18"), "#423C2E")

    def test_permille_of_a_tint(self):
        self.assertEqual(P.resolve("tint.diag"), "0.12")
        self.assertEqual(f(P.resolve("tint.diag"), "permille"), "120")
        self.assertEqual(f("0.2", "permille"), "200")
        with self.assertRaisesRegex(filters.FilterError, "three decimals"):
            f("0.1234", "permille")
        with self.assertRaisesRegex(filters.FilterError, "expects a number"):
            f("#88B0B4", "permille")

    def test_errors(self):
        with self.assertRaisesRegex(filters.FilterError, "unknown filter"):
            f("#88B0B4", "shout")
        with self.assertRaisesRegex(filters.FilterError, "expects a #RRGGBB"):
            f("88B0B4", "nohash")
        with self.assertRaisesRegex(filters.FilterError, "alpha"):
            f("#88B0B4", "alpha", "4")
        with self.assertRaisesRegex(filters.FilterError, "channel"):
            f("#88B0B4", "channel", "x")
        with self.assertRaisesRegex(filters.FilterError, "no arguments"):
            f("#88B0B4", "lower", "x")
        with self.assertRaisesRegex(filters.FilterError, "not a color"):
            f("#88B0B4", "blend", "meta.slug", "0.5")
        with self.assertRaisesRegex(filters.FilterError, "expects a #RRGGBB"):
            f("#88B0B4\n", "nohash")

if __name__ == "__main__":
    unittest.main()
