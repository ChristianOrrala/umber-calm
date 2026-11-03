"""Moshi (iOS): the paste string and the QR code, both derived from the rendered theme JSON.

Moshi imports a theme from a `moshi://theme?d=<payload>` link (what the QR code holds) or from a pasted
`moshi-theme:<payload>` string; the payload is the compact JSON in base64url without padding, as the links of
Moshi's own theme gallery (getmoshi.app/themes) carry it."""
from __future__ import annotations

import base64
import json

from . import qr
from .outputs import BuildError
from .palette import Palette

THEME = "ports/moshi/umber-calm.json"
PASTE = "ports/moshi/umber-calm-import.txt"
QR = "ports/moshi/umber-calm-qr.svg"


def payload(theme: bytes) -> str:
    compact = json.dumps(json.loads(theme.decode("utf-8")), separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(compact.encode("utf-8")).decode("ascii").rstrip("=")


def plan(planned: dict[str, tuple[str, bytes]], pal: Palette) -> dict[str, tuple[str, bytes]]:
    """The paste string and the QR code for the planned theme, owned by the theme's port (so the port's digest
    covers them). Empty when no theme is planned."""
    entry = planned.get(THEME)
    if entry is None:
        return {}
    for rel in (PASTE, QR):
        if rel in planned:
            raise BuildError(f"collision: {rel!r} is derived from {THEME!r}; a template must not write it")
    owner, theme = entry
    encoded = payload(theme)
    matrix = qr.encode(f"moshi://theme?d={encoded}".encode("ascii"))
    return {PASTE: (owner, f"moshi-theme:{encoded}\n".encode("ascii")),
            QR: (owner, qr.svg(matrix, dark=pal.colors["bg"], light=pal.colors["text_bright"]).encode("ascii"))}
