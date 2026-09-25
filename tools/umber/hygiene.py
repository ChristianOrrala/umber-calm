"""Generic repository hygiene patterns (spec §8.1 item 6), shared by checks and mark.

Findings name the location and the pattern, never the matched text: CI logs are public.
"""
from __future__ import annotations

import re
import struct
import zlib

# Every pattern is linear-time on any input: a match may only START where its run of characters starts (a
# lookbehind rejects every inner position in O(1)), and every repetition is bounded (local part {1,64}, labels
# {1,63}), so a megabyte of word characters, base64 or minified code costs one pass.
EMAIL = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]{1,64}@(?:[A-Za-z0-9-]{1,63}\.){1,8}[A-Za-z]{2,63}(?![A-Za-z0-9-])")
ALLOWED_EMAIL_SUFFIXES = ("@users.noreply.github.com",)
ALLOWED_EMAILS = ("noreply@github.com",)
HYGIENE_PATTERNS = [
    ("home path", re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+")),
    ("Windows home path", re.compile(r"\b[A-Za-z]:(?:\\\\?|/)Users(?:\\\\?|/)[^\\/\s\"']+")),
    ("local hostname", re.compile(r"(?<![A-Za-z0-9-])[A-Za-z0-9-]{1,63}\.local\b")),
    ("private IP", re.compile(r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b")),
]

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# Text (tEXt, zTXt, iTXt, which is also where XMP lives), EXIF and timestamp chunks: images ship without metadata.
PNG_METADATA_CHUNKS = {b"tEXt", b"iTXt", b"zTXt", b"eXIf", b"tIME"}


def email_allowed(address: str) -> bool:
    return address in ALLOWED_EMAILS or address.endswith(ALLOWED_EMAIL_SUFFIXES)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def scan_text(text: str, where: str) -> list[str]:
    found = []
    for label, pattern in HYGIENE_PATTERNS:
        for m in pattern.finditer(text):
            found.append(f"hygiene: {label} in {where}:{line_of(text, m.start())}")
    for m in EMAIL.finditer(text):
        if not email_allowed(m.group(0)):
            found.append(f"hygiene: email in {where}:{line_of(text, m.start())}")
    return found


def png_problems(data: bytes, where: str) -> list[str]:
    """A PNG must parse chunk by chunk (valid CRCs, IHDR first), carry no metadata chunks and end at IEND."""
    if not data.startswith(PNG_SIGNATURE):
        return [f"hygiene: {where} is not a PNG file"]
    pos, metadata = len(PNG_SIGNATURE), []
    while True:
        if pos + 12 > len(data):
            return [f"hygiene: {where} is a malformed PNG (truncated chunk)"]
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind, end = data[pos + 4:pos + 8], pos + 12 + length
        if end > len(data):
            return [f"hygiene: {where} is a malformed PNG (truncated chunk)"]
        if zlib.crc32(data[pos + 4:end - 4]) & 0xFFFFFFFF != struct.unpack(">I", data[end - 4:end])[0]:
            return [f"hygiene: {where} is a malformed PNG (chunk CRC mismatch)"]
        if pos == len(PNG_SIGNATURE) and kind != b"IHDR":
            return [f"hygiene: {where} is a malformed PNG (does not start with IHDR)"]
        if kind in PNG_METADATA_CHUNKS:
            metadata.append(kind.decode("ascii"))
        pos = end
        if kind == b"IEND":
            break
    found = [f"hygiene: {where} has PNG metadata chunks {sorted(set(metadata))}"] if metadata else []
    if pos < len(data):
        found.append(f"hygiene: {where} has {len(data) - pos} bytes after IEND")
    return found
