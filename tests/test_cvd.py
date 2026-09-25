import itertools, unittest
from tests.helpers import load_real_palette
from umber import cvd

class CvdTest(unittest.TestCase):
    def test_grayscale_is_neutral(self):
        g = cvd.simulate("#88B0B4", "grayscale")
        self.assertEqual(g[1:3], g[3:5]); self.assertEqual(g[3:5], g[5:7])

    def test_black_and_white_are_fixed_points(self):
        for kind in cvd.KINDS:
            self.assertEqual(cvd.simulate("#000000", kind), "#000000")
            self.assertEqual(cvd.simulate("#FFFFFF", kind), "#FFFFFF")

    def test_report_lists_every_accent_and_every_pair(self):
        text = cvd.report(load_real_palette())
        for name in cvd.ACCENTS:
            self.assertIn(f"| `{name}` |", text)
        for a, b in itertools.combinations(cvd.ACCENTS, 2):
            self.assertTrue(f"| {a} / {b} |" in text or f"| {b} / {a} |" in text, (a, b))
        self.assertIn("(renders/grayscale.svg)", text)

if __name__ == "__main__":
    unittest.main()
