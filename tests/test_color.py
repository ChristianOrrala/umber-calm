import unittest
from fractions import Fraction

import tests  # noqa: F401 — puts tools/ on sys.path
from umber import color

class ColorTest(unittest.TestCase):
    def test_parse_and_format(self):
        self.assertEqual(color.parse_hex("#88b0b4"), (136, 176, 180))
        self.assertEqual(color.to_hex((136, 176, 180)), "#88B0B4")
        for bad in ("88B0B4", "#88B0B", "#GGGGGG", "#88B0B44D", "#88B0B4\n", None):
            with self.assertRaises(ValueError):
                color.parse_hex(bad)

    def test_contrast_matches_spec(self):
        self.assertEqual(round(color.contrast("#D6C9B6", "#201F1D"), 2), 10.11)
        self.assertEqual(round(color.contrast("#938A7B", "#201F1D"), 2), 4.83)
        self.assertEqual(round(color.contrast("#6E6961", "#201F1D"), 2), 3.02)
        self.assertEqual(color.contrast("#201F1D", "#D6C9B6"), color.contrast("#D6C9B6", "#201F1D"))

    def test_blend_known_values(self):
        self.assertEqual(color.blend("#DCC07D", "#201F1D", 0.18), "#423C2E")
        self.assertEqual(color.blend("#A7B56E", "#201F1D", 0.22), "#3E402F")
        self.assertEqual(color.blend("#EDA97C", "#201F1D", color.alpha_fraction("4D")), "#5E493A")
        self.assertEqual(color.blend("#FFFFFF", "#000000", 0.0), "#000000")
        self.assertEqual(color.blend("#FFFFFF", "#000000", 1.0), "#FFFFFF")
        with self.assertRaises(ValueError):
            color.blend("#FFFFFF", "#000000", 1.5)

    def test_blend_rounds_half_up_exactly(self):
        # 0.9*0 + 0.1*5 is exactly 0.5 per channel; float arithmetic gives 0.4999… and would round to 0.
        self.assertEqual(color.blend("#000000", "#050505", 0.9), "#010101")
        self.assertEqual(color.blend("#000000", "#050505", Fraction(9, 10)), "#010101")
        self.assertEqual(color.blend("#000000", "#030303", 0.5), "#020202")  # 1.5 -> 2

    def test_alpha_fraction_is_exact(self):
        self.assertEqual(color.alpha_fraction("4D"), Fraction(77, 255))
        with self.assertRaises(ValueError):
            color.alpha_fraction("4")

    def test_delta_e_ok(self):
        self.assertEqual(round(color.delta_e_ok("#6E6961", "#938A7B"), 1), 11.5)
        self.assertEqual(round(color.delta_e_ok("#EDA97C", "#DCC07D"), 1), 6.2)

    def test_ansi256(self):
        self.assertEqual(color.ansi256("#88B0B4"), 109)
        self.assertEqual(color.ansi256("#201F1D"), 234)

if __name__ == "__main__":
    unittest.main()
