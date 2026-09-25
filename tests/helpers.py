import tempfile
from pathlib import Path

import tests  # noqa: F401 — puts tools/ on sys.path

REPO = Path(__file__).resolve().parents[1]
PALETTE_PATH = REPO / "palette" / "umber-calm.toml"

from umber import palette as _palette  # noqa: E402


def load_real_palette():
    return _palette.load(PALETTE_PATH)


def write_temp_palette(tmpdir: str, replacements: dict[str, str]) -> Path:
    text = PALETTE_PATH.read_text(encoding="utf-8")
    for old, new in replacements.items():
        if old not in text:
            raise AssertionError(f"fixture replacement target not found: {old!r}")
        text = text.replace(old, new, 1)
    path = Path(tmpdir) / "palette.toml"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def tempdir():
    return tempfile.TemporaryDirectory()
