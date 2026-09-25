"""Load, validate, and resolve references against the palette file."""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from . import color

CONTRACTS = ("syntax", "ui", "diag", "term")
RESERVED_SYNTAX = ("red", "orange")
ANSI_SLOTS = tuple(f"{prefix}{name}" for prefix in ("", "bright_")
                   for name in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"))
SEMVER_RE = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
META_TYPES = {"name": str, "slug": str, "palette_version": str, "release": str, "schema_version": int,
              "license": str, "author": str, "homepage": str}
META_KEYS = tuple(META_TYPES)
REQUIRED_ROLES = {
    "syntax": ("keyword", "preproc", "function", "tag", "type", "namespace", "attribute", "string", "escape",
               "constant", "builtin", "variable", "operator", "comment", "heading", "link", "code"),
    "ui": ("bg", "surface", "chrome", "selection_bg", "selection_fg", "border_strong", "border", "text",
           "text_secondary", "line_number", "line_number_active", "text_dim", "focus"),
    "diag": ("error", "warning", "info", "hint", "ok", "diff_add", "diff_delete", "diff_change", "search"),
    "term": ("background", "foreground", "cursor", "cursor_text", "selection_bg", "selection_fg"),
}
REQUIRED_TINTS = ("diag", "diff", "search")


class PaletteError(ValueError):
    pass


@dataclass(frozen=True)
class Palette:
    meta: dict
    colors: dict[str, str]
    ansi: dict[str, str]
    roles: dict[str, dict[str, str]]
    tints: dict[str, float]

    def resolve(self, ref: str) -> str:
        if ref in self.colors:
            return self.colors[ref]
        namespace, _, name = ref.partition(".")
        if namespace == "ansi" and name in self.ansi:
            return self.ansi[name]
        if namespace in self.roles and name in self.roles[namespace]:
            return self.colors[self.roles[namespace][name]]
        if namespace == "meta" and name in self.meta:
            return str(self.meta[name])
        if namespace == "tint" and name in self.tints:
            return str(self.tints[name])  # e.g. "0.12"; `permille` turns it into 120
        raise PaletteError(f"unknown reference {ref!r}")

    def is_color_value(self, ref: str) -> bool:
        """True when `ref` resolves to a #RRGGBB color (colors, roles, ANSI slots; not meta)."""
        try:
            return color.is_hex(self.resolve(ref))
        except PaletteError:
            return False

    def tint(self, value: str) -> float:
        if value.startswith("tint."):
            name = value[len("tint."):]
            if name not in self.tints:
                raise PaletteError(f"unknown tint {value!r}")
            return self.tints[name]
        try:
            t = float(value)
        except ValueError:
            raise PaletteError(f"invalid blend amount {value!r}") from None
        if not 0.0 <= t <= 1.0:
            raise PaletteError(f"blend amount {value!r} is outside 0..1")
        return t


def _hex_or_name(value: str, colors: dict[str, str], where: str) -> str:
    if isinstance(value, str) and value.startswith("#"):
        try:
            color.parse_hex(value)
        except ValueError as e:
            raise PaletteError(f"{where}: {e}") from None
        return value.upper()
    if value in colors:
        return colors[value]
    raise PaletteError(f"{where}: unknown color {value!r}")


def _check_meta(meta: dict) -> None:
    for key, kind in META_TYPES.items():
        if key not in meta:
            raise PaletteError(f"[meta] is missing {key!r}")
        value = meta[key]
        if not isinstance(value, kind) or isinstance(value, bool):
            raise PaletteError(f"[meta] {key}: expected {kind.__name__}, got {value!r}")
    for key in ("palette_version", "release"):
        if not SEMVER_RE.fullmatch(meta[key]):
            raise PaletteError(f"[meta] {key}: {meta[key]!r} is not MAJOR.MINOR.PATCH")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", meta["slug"]):
        raise PaletteError(f"[meta] slug: {meta['slug']!r} must be lowercase letters, digits and hyphens")
    if not meta["homepage"].startswith("https://"):
        raise PaletteError("[meta] homepage must be an https:// URL")


def load(path: Path) -> Palette:
    try:
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise PaletteError(f"{path}: {e}") from None

    meta = data.get("meta", {})
    _check_meta(meta)

    colors: dict[str, str] = {}
    for name, value in data.get("colors", {}).items():
        try:
            color.parse_hex(value)
        except ValueError as e:
            raise PaletteError(f"[colors] {name}: {e}") from None
        colors[name] = value.upper()

    ansi_raw = data.get("ansi", {})
    for slot in ANSI_SLOTS:
        if slot not in ansi_raw:
            raise PaletteError(f"[ansi] is missing {slot!r}")
    extra = set(ansi_raw) - set(ANSI_SLOTS)
    if extra:
        raise PaletteError(f"[ansi] has unknown slots {sorted(extra)}")
    ansi = {slot: _hex_or_name(ansi_raw[slot], colors, f"[ansi] {slot}") for slot in ANSI_SLOTS}

    roles_raw = data.get("roles", {})
    roles: dict[str, dict[str, str]] = {}
    for contract in CONTRACTS:
        entries = roles_raw.get(contract) or {}
        for role in REQUIRED_ROLES[contract]:
            if role not in entries:
                raise PaletteError(f"[roles.{contract}] is missing {role!r}")
        for role, name in entries.items():
            if name not in colors:
                raise PaletteError(f"[roles.{contract}] {role}: unknown color {name!r}")
        roles[contract] = dict(entries)
    reserved_hex = {colors[n] for n in RESERVED_SYNTAX if n in colors}
    for role, name in roles["syntax"].items():
        if name in RESERVED_SYNTAX or colors[name] in reserved_hex:
            raise PaletteError(f"[roles.syntax] {role}: {name!r} is reserved (red = errors, orange = focus)")

    tints: dict[str, float] = {}
    for name, value in data.get("tints", {}).items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
            raise PaletteError(f"[tints] {name}: must be a number between 0 and 1")
        if (color.exact(value) * 1000).denominator != 1:
            raise PaletteError(f"[tints] {name}: at most three decimals (Neovim blends in per-mille integers)")
        tints[name] = float(value)
    for name in REQUIRED_TINTS:
        if name not in tints:
            raise PaletteError(f"[tints] is missing {name!r}")

    return Palette(meta=dict(meta), colors=colors, ansi=ansi, roles=roles, tints=tints)
