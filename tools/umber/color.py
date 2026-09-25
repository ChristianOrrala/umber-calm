"""Color math: hex parsing, WCAG contrast, exact sRGB blending, OKLab distance, xterm-256."""
from __future__ import annotations

import math
import re
from fractions import Fraction

HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")  # always use HEX_RE.fullmatch


def is_hex(value: object) -> bool:
    return isinstance(value, str) and HEX_RE.fullmatch(value) is not None


def parse_hex(h: str) -> tuple[int, int, int]:
    if not is_hex(h):
        raise ValueError(f"invalid color {h!r}; expected #RRGGBB")
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


def to_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % rgb


def _linear(channel: int) -> float:
    c = channel / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(h: str) -> float:
    r, g, b = (_linear(c) for c in parse_hex(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def exact(t: float | Fraction | str) -> Fraction:
    """A blend amount as an exact fraction. Floats go through their shortest decimal repr (0.9 -> 9/10)."""
    if isinstance(t, Fraction):
        return t
    if isinstance(t, bool):
        raise ValueError(f"invalid blend amount {t!r}")
    return Fraction(str(t)) if isinstance(t, (int, float)) else Fraction(t)


def blend(fg: str, bg: str, t: float | Fraction | str) -> str:
    """Composite `t` of fg over bg per sRGB channel, rounding half up, in exact rational arithmetic."""
    amount = exact(t)
    if not 0 <= amount <= 1:
        raise ValueError(f"blend amount {t} is outside 0..1")
    f, b = parse_hex(fg), parse_hex(bg)
    half = Fraction(1, 2)
    return to_hex(tuple(math.floor(amount * x + (1 - amount) * y + half) for x, y in zip(f, b)))


def alpha_fraction(aa: str) -> Fraction:
    if not isinstance(aa, str) or not re.fullmatch(r"[0-9A-Fa-f]{2}", aa):
        raise ValueError(f"invalid alpha {aa!r}; expected two hex digits")
    return Fraction(int(aa, 16), 255)


def _oklab(h: str) -> tuple[float, float, float]:
    r, g, b = (_linear(c) for c in parse_hex(h))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def delta_e_ok(a: str, b: str) -> float:
    return 100 * math.dist(_oklab(a), _oklab(b))


_LEVELS = (0, 95, 135, 175, 215, 255)


def _xterm(index: int) -> tuple[int, int, int]:
    if index >= 232:
        v = 8 + 10 * (index - 232)
        return (v, v, v)
    i = index - 16
    return (_LEVELS[i // 36], _LEVELS[(i % 36) // 6], _LEVELS[i % 6])


def ansi256(h: str) -> int:
    target = parse_hex(h)
    return min(range(16, 256),
               key=lambda i: (sum((a - b) ** 2 for a, b in zip(target, _xterm(i))), i))
