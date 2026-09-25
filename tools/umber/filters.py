"""Template filters. Filters chain left to right; color filters need a #RRGGBB input."""
from __future__ import annotations

import re
from fractions import Fraction

from . import color
from .palette import Palette, PaletteError

NAMES = frozenset({"lower", "nohash", "alpha", "rgba_nohash", "argb", "blend",
                   "rgb_decimal", "channel", "ansi256", "colorname", "permille"})


class FilterError(ValueError):
    pass


def _need_hex(value: str, name: str) -> tuple[int, int, int]:
    if not color.is_hex(value):
        raise FilterError(f"filter {name!r} expects a #RRGGBB color, got {value!r}")
    return color.parse_hex(value)


def _no_args(args: list[str], name: str) -> None:
    if args:
        raise FilterError(f"filter {name!r} takes no arguments")


def _alpha(args: list[str], name: str) -> str:
    if len(args) != 1 or not re.fullmatch(r"[0-9A-Fa-f]{2}", args[0]):
        raise FilterError(f"filter {name!r} expects one two-digit hex alpha, e.g. {name}(4D)")
    return args[0].upper()


def apply(value: str, name: str, args: list[str], pal: Palette) -> str:
    if name not in NAMES:
        raise FilterError(f"unknown filter {name!r}")
    if name == "lower":
        _no_args(args, name)
        return value.lower()
    if name == "nohash":
        _no_args(args, name)
        _need_hex(value, name)
        return value[1:]
    if name == "rgb_decimal":
        _no_args(args, name)
        return ",".join(str(c) for c in _need_hex(value, name))
    if name == "ansi256":
        _no_args(args, name)
        _need_hex(value, name)
        return str(color.ansi256(value))
    if name in ("alpha", "rgba_nohash", "argb"):
        _need_hex(value, name)
        a = _alpha(args, name)
        return {"alpha": value + a, "rgba_nohash": value[1:] + a, "argb": "#" + a + value[1:]}[name]
    if name == "channel":
        rgb = _need_hex(value, name)
        if len(args) != 1 or args[0] not in ("r", "g", "b"):
            raise FilterError("filter 'channel' expects one of r, g, b")
        return f"{rgb['rgb'.index(args[0])] / 255:.6f}"
    if name == "permille":
        _no_args(args, name)
        try:
            amount = Fraction(value) * 1000
        except ValueError:
            raise FilterError(f"filter 'permille' expects a number such as a tint, got {value!r}") from None
        if amount.denominator != 1:
            raise FilterError(f"filter 'permille': {value} has more than three decimals")
        return str(amount.numerator)
    if name == "colorname":
        _no_args(args, name)
        _need_hex(value, name)
        matches = sorted(n for n, hx in pal.colors.items() if hx == value.upper())
        if len(matches) > 1:
            raise FilterError(f"filter 'colorname': {value} matches several colors {matches}")
        return matches[0] if matches else value.upper()
    # blend
    _need_hex(value, name)
    if len(args) != 2:
        raise FilterError("filter 'blend' expects (base color, amount)")
    if not pal.is_color_value(args[0]):
        raise FilterError(f"filter 'blend': base {args[0]!r} is not a color")
    try:
        amount = pal.tint(args[1])
    except PaletteError as e:
        raise FilterError(f"filter 'blend': {e}") from None
    return color.blend(value, pal.resolve(args[0]), amount)
