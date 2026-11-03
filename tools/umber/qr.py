"""A QR code encoder: byte mode, error correction level M, versions 1 to 40 (ISO/IEC 18004). Standard library only.

It follows the structure of Project Nayuki's reference encoder (MIT): pick the smallest version, add Reed-Solomon
error correction per block, interleave, draw the function patterns and the data, then keep the mask with the lowest
penalty. tests/test_qr.py compares its matrices with an independent encoder's."""
from __future__ import annotations

from collections import deque

QUIET_ZONE = 4  # modules of light border the standard asks for around the symbol

# Level M, indexed by version (index 0 unused): error correction codewords per block, and the number of blocks.
ECC_PER_BLOCK = (0, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26,
                 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28)
BLOCKS = (0, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16,
          17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49)
FORMAT_LEVEL_M = 0b00
BYTE_MODE = 0b0100


def _raw_modules(version: int) -> int:
    """Modules left for data and error correction once the function patterns are drawn."""
    result = (16 * version + 128) * version + 64
    if version >= 2:
        n = version // 7 + 2
        result -= (25 * n - 10) * n - 55
        if version >= 7:
            result -= 36
    return result


def _data_codewords(version: int) -> int:
    return _raw_modules(version) // 8 - ECC_PER_BLOCK[version] * BLOCKS[version]


def _data_bits(length: int, version: int) -> int:
    return 4 + (8 if version <= 9 else 16) + 8 * length


def version_for(length: int) -> int:
    """The smallest version that holds `length` bytes at level M."""
    for version in range(1, 41):
        if _data_bits(length, version) <= _data_codewords(version) * 8:
            return version
    raise ValueError(f"data too long for a QR code at level M: {length} bytes")


def _gf_mul(x: int, y: int) -> int:
    """Multiplication in GF(2^8) modulo x^8 + x^4 + x^3 + x^2 + 1."""
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(degree: int) -> list[int]:
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = _gf_mul(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = _gf_mul(root, 0x02)
    return result


def _rs_remainder(data: list[int], divisor: list[int]) -> list[int]:
    result = [0] * len(divisor)
    for b in data:
        factor = b ^ result.pop(0)
        result.append(0)
        for i, coefficient in enumerate(divisor):
            result[i] ^= _gf_mul(coefficient, factor)
    return result


def _codewords(data: bytes, version: int) -> list[int]:
    """Data codewords (mode, count, bytes, terminator, padding), split into blocks, with error correction, interleaved."""
    bits: list[int] = []

    def put(value: int, width: int) -> None:
        bits.extend((value >> i) & 1 for i in reversed(range(width)))

    put(BYTE_MODE, 4)
    put(len(data), 8 if version <= 9 else 16)
    for b in data:
        put(b, 8)
    capacity = _data_codewords(version) * 8
    put(0, min(4, capacity - len(bits)))
    put(0, -len(bits) % 8)
    pad = 0xEC
    while len(bits) < capacity:
        put(pad, 8)
        pad ^= 0xEC ^ 0x11
    words = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]

    n_blocks, ecc_len = BLOCKS[version], ECC_PER_BLOCK[version]
    raw = _raw_modules(version) // 8
    short_blocks = n_blocks - raw % n_blocks
    short_len = raw // n_blocks
    divisor = _rs_divisor(ecc_len)
    blocks, k = [], 0
    for i in range(n_blocks):
        size = short_len - ecc_len + (0 if i < short_blocks else 1)
        block = words[k:k + size]
        k += size
        ecc = _rs_remainder(block, divisor)
        if i < short_blocks:
            block.append(0)  # placeholder, skipped when interleaving
        blocks.append(block + ecc)
    result = []
    for i in range(len(blocks[0])):
        for j, block in enumerate(blocks):
            if i != short_len - ecc_len or j >= short_blocks:
                result.append(block[i])
    return result


class _Symbol:
    def __init__(self, version: int):
        self.version = version
        self.size = version * 4 + 17
        self.modules = [[False] * self.size for _ in range(self.size)]
        self.function = [[False] * self.size for _ in range(self.size)]

    def set(self, x: int, y: int, dark: bool) -> None:
        self.modules[y][x] = dark
        self.function[y][x] = True

    def alignment_positions(self) -> list[int]:
        if self.version == 1:
            return []
        n = self.version // 7 + 2
        step = (self.version * 8 + n * 3 + 5) // (n * 4 - 4) * 2
        return [6] + [self.size - 7 - i * step for i in reversed(range(n - 1))]

    def draw_function_patterns(self) -> None:
        for i in range(self.size):
            self.set(6, i, i % 2 == 0)
            self.set(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (self.size - 4, 3), (3, self.size - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < self.size and 0 <= y < self.size:
                        self.set(x, y, max(abs(dx), abs(dy)) not in (2, 4))
        positions = self.alignment_positions()
        last = len(positions) - 1
        for i, px in enumerate(positions):
            for j, py in enumerate(positions):
                if (i, j) in ((0, 0), (0, last), (last, 0)):
                    continue  # under a finder pattern
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self.set(px + dx, py + dy, max(abs(dx), abs(dy)) != 1)
        self.draw_format_bits(0)  # reserves the format areas; drawn again with the chosen mask
        self.draw_version()

    def draw_format_bits(self, mask: int) -> None:
        data = FORMAT_LEVEL_M << 3 | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412
        bit = lambda i: (bits >> i) & 1 == 1  # noqa: E731
        for i in range(6):
            self.set(8, i, bit(i))
        self.set(8, 7, bit(6))
        self.set(8, 8, bit(7))
        self.set(7, 8, bit(8))
        for i in range(9, 15):
            self.set(14 - i, 8, bit(i))
        for i in range(8):
            self.set(self.size - 1 - i, 8, bit(i))
        for i in range(8, 15):
            self.set(8, self.size - 15 + i, bit(i))
        self.set(8, self.size - 8, True)  # the dark module

    def draw_version(self) -> None:
        if self.version < 7:
            return
        rem = self.version
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        bits = self.version << 12 | rem
        for i in range(18):
            dark = (bits >> i) & 1 == 1
            a, b = self.size - 11 + i % 3, i // 3
            self.set(a, b, dark)
            self.set(b, a, dark)

    def draw_codewords(self, words: list[int]) -> None:
        i, total = 0, len(words) * 8
        right = self.size - 1
        while right >= 1:
            if right == 6:
                right = 5
            upward = (right + 1) & 2 == 0
            for vert in range(self.size):
                y = self.size - 1 - vert if upward else vert
                for x in (right, right - 1):
                    if not self.function[y][x] and i < total:
                        self.modules[y][x] = (words[i >> 3] >> (7 - (i & 7))) & 1 == 1
                        i += 1
            right -= 2

    def apply_mask(self, mask: int) -> None:
        rule = MASKS[mask]
        for y in range(self.size):
            for x in range(self.size):
                if not self.function[y][x] and rule(x, y):
                    self.modules[y][x] = not self.modules[y][x]

    def penalty(self) -> int:
        size, modules = self.size, self.modules
        result = 0
        for lines in (modules, [list(col) for col in zip(*modules)]):
            for line in lines:
                run_color, run, history = False, 0, deque([0] * 7, 7)
                for dark in line:
                    if dark == run_color:
                        run += 1
                        if run == 5:
                            result += 3
                        elif run > 5:
                            result += 1
                    else:
                        self._add_history(run, history)
                        if not run_color:
                            result += self._finder_like(history) * 40
                        run_color, run = dark, 1
                result += self._terminate(run_color, run, history) * 40
        for y in range(size - 1):
            for x in range(size - 1):
                if modules[y][x] == modules[y][x + 1] == modules[y + 1][x] == modules[y + 1][x + 1]:
                    result += 3
        dark = sum(row.count(True) for row in modules)
        total = size * size
        result += ((abs(dark * 20 - total * 10) + total - 1) // total - 1) * 10
        return result

    def _add_history(self, run: int, history: deque) -> None:
        if history[0] == 0:
            run += self.size  # the light border before the first run
        history.appendleft(run)

    def _finder_like(self, history: deque) -> int:
        n = history[1]
        core = n > 0 and history[2] == history[4] == history[5] == n and history[3] == n * 3
        return int(core and history[0] >= n * 4 and history[6] >= n) + int(core and history[6] >= n * 4 and history[0] >= n)

    def _terminate(self, run_color: bool, run: int, history: deque) -> int:
        if run_color:
            self._add_history(run, history)
            run = 0
        self._add_history(run + self.size, history)  # the light border after the last run
        return self._finder_like(history)


MASKS = (
    lambda x, y: (x + y) % 2 == 0,
    lambda x, y: y % 2 == 0,
    lambda x, y: x % 3 == 0,
    lambda x, y: (x + y) % 3 == 0,
    lambda x, y: (x // 3 + y // 2) % 2 == 0,
    lambda x, y: x * y % 2 + x * y % 3 == 0,
    lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
    lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
)


def encode(data: bytes) -> list[list[bool]]:
    """The symbol for `data` as rows of modules (True is dark), without the quiet zone."""
    version = version_for(len(data))
    symbol = _Symbol(version)
    symbol.draw_function_patterns()
    symbol.draw_codewords(_codewords(data, version))
    best, best_penalty = 0, None
    for mask in range(8):
        symbol.apply_mask(mask)
        symbol.draw_format_bits(mask)
        score = symbol.penalty()
        if best_penalty is None or score < best_penalty:
            best, best_penalty = mask, score
        symbol.apply_mask(mask)  # XOR again: undo
    symbol.apply_mask(best)
    symbol.draw_format_bits(best)
    return symbol.modules


def svg(matrix: list[list[bool]], *, dark: str, light: str) -> str:
    """A crisp SVG of `matrix` with the quiet zone: one rectangle for the light field, one path of dark runs."""
    side = len(matrix) + 2 * QUIET_ZONE
    runs = []
    for y, row in enumerate(matrix):
        x = 0
        while x < len(row):
            if row[x]:
                start = x
                while x < len(row) and row[x]:
                    x += 1
                n = x - start
                runs.append(f"M{start + QUIET_ZONE} {y + QUIET_ZONE}h{n}v1h-{n}z")
            else:
                x += 1
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" width="{side * 4}" '
            f'height="{side * 4}" shape-rendering="crispEdges">'
            f'<rect width="{side}" height="{side}" fill="{light}"/>'
            f'<path fill="{dark}" d="{"".join(runs)}"/></svg>\n')
