"""The QR encoder (byte mode, error correction level M) against matrices from an independent encoder."""
import re, unittest
import xml.etree.ElementTree as ET
from tests.helpers import REPO
from umber import qr

# ISO/IEC 18004 byte-mode capacity at level M, versions 1 to 40 (the same numbers segno 1.6.6 accepts).
CAPACITY_M = [14, 26, 42, 62, 84, 106, 122, 152, 180, 213, 251, 287, 331, 362, 412, 450, 504, 560, 624, 666,
              711, 779, 857, 911, 997, 1059, 1125, 1190, 1264, 1370, 1452, 1538, 1628, 1722, 1809, 1911, 1989,
              2099, 2213, 2331]

# tests/fixtures/qr-m-*.txt: Project Nayuki's qrcodegen 1.8.0 at level MEDIUM without boosting, one row per line
# (the header names the version and mask it chose). segno is not used for them: in byte mode it writes an extra
# 0x00 codeword after the terminator, a valid symbol but not the same bytes.
GOLDEN = {
    "qr-m-v1.txt": b"Umber Calm",
    "qr-m-v2.txt": b"Umber Calm 0.3.",   # 15 bytes: one past version 1's 14
    "qr-m-v7.txt": b"0123456789" * 12,   # version 7: the first with version information
    "qr-m-v20.txt": b"Umber Calm " * 60,  # version 20: 16 blocks of two lengths, interleaved
}


def golden(name: str) -> list[list[bool]]:
    rows = (REPO / "tests/fixtures" / name).read_text(encoding="utf-8").splitlines()
    return [[c == "1" for c in row] for row in rows if not row.startswith("#")]


def cells(svg: str) -> set[tuple[int, int]]:
    """The dark cells an SVG from qr.svg draws, read back from its path."""
    path = ET.fromstring(svg).find("{http://www.w3.org/2000/svg}path").get("d")
    found = set()
    for x, y, n in re.findall(r"M(\d+) (\d+)h(\d+)v1h-\3z", path):
        found.update((int(x) + i, int(y)) for i in range(int(n)))
    return found


class Encode(unittest.TestCase):
    def test_matches_reference_matrices(self):
        for name, data in GOLDEN.items():
            with self.subTest(name):
                self.assertEqual(qr.encode(data), golden(name))

    def test_smallest_version_that_holds_the_data(self):
        for version, capacity in enumerate(CAPACITY_M, 1):
            self.assertEqual(qr.version_for(capacity), version)
            if version < 40:
                self.assertEqual(qr.version_for(capacity + 1), version + 1)

    def test_refuses_data_past_version_40(self):
        with self.assertRaisesRegex(ValueError, "too long"):
            qr.version_for(CAPACITY_M[-1] + 1)


class Svg(unittest.TestCase):
    def test_draws_every_dark_module_inside_the_quiet_zone(self):
        matrix = qr.encode(b"Umber Calm")
        svg = qr.svg(matrix, dark="#201F1D", light="#EDE3D2")
        root = ET.fromstring(svg)
        side = len(matrix) + 2 * qr.QUIET_ZONE
        self.assertEqual(root.get("viewBox"), f"0 0 {side} {side}")
        self.assertEqual(root.find("{http://www.w3.org/2000/svg}rect").get("fill"), "#EDE3D2")
        self.assertEqual(root.find("{http://www.w3.org/2000/svg}path").get("fill"), "#201F1D")
        expected = {(x + qr.QUIET_ZONE, y + qr.QUIET_ZONE)
                    for y, row in enumerate(matrix) for x, dark in enumerate(row) if dark}
        self.assertEqual(cells(svg), expected)

    def test_is_deterministic(self):
        matrix = qr.encode(b"Umber Calm")
        self.assertEqual(qr.svg(matrix, dark="#000000", light="#FFFFFF"),
                         qr.svg(qr.encode(b"Umber Calm"), dark="#000000", light="#FFFFFF"))


if __name__ == "__main__":
    unittest.main()
