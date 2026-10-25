"""The VS Code Marketplace and Open VSX listing pages, with the SVG sources of their icon and palette strip.
Standard library only. The pages link committed PNGs (listings refuse SVG images) at the release tag."""
from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from pathlib import Path

from . import color, safepath
from .palette import Palette
from .sessions import MONO

OWNER = "docs"
PUBLISHER = "ChristianOrrala"
ACCENTS = ("red", "orange", "yellow", "green", "cyan", "blue", "purple")
PAGES = {"vscode": "docs/marketplace/vscode.md", "kiro": "docs/marketplace/kiro.md"}
IMAGE_DIR = "assets/marketplace"
SOURCES = "assets/marketplace/sources.json"
IMAGES = {"icon": "docs/marketplace/icon.svg", "palette": "docs/marketplace/palette.svg",
          "editor": "docs/renders/session-editor.svg", "terminal": "docs/renders/session-terminal.svg",
          "claude": "docs/renders/session-claude.svg", "color-vision": "docs/renders/color-vision.svg",
          "vscode-hero": "ports/vscode/themes/umber-calm-color-theme.json"}
IMAGE_NAME = re.compile(r"/assets/marketplace/([a-z0-9-]+)\.png")
EPSILON = 1e-9  # a ratio stored as 9.2999999 still reads 9.3
ICON_MIN = 128  # the Marketplace's smallest accepted icon, in pixels on each side

STRIP_ORDER = (("yellow", "keywords"), ("blue", "functions"), ("cyan", "types"), ("green", "strings"),
               ("purple", "constants"), ("red", "errors"), ("orange", "focus"))
RAMP = ("bg_dim", "bg", "surface", "overlay", "muted", "subtle", "text", "text_bright")
STRIP_W, STRIP_H, PAD, GAP = 760, 168, 16, 10

# Per-port differences; everything else on the two pages is shared.
VARIANTS = {
    "vscode": {
        "title": "Umber Calm", "app": "VS Code", "sibling": "Kiro", "hero": "vscode-hero",
        "hero_alt": "Umber Calm in VS Code: the explorer, an open TypeScript file and the status bar",
        "try": f"[Try it in your browser](https://vscode.dev/theme/{PUBLISHER}.umber-calm/Umber%20Calm), "
               "no install needed.",
        "install": (
            '1. Click **Install** above, or search for "Umber Calm" in the Extensions view.\n'
            "2. Press Cmd/Ctrl+K Cmd/Ctrl+T and choose **Umber Calm**.\n\n"
            f"Using Kiro? Install [Umber Calm for Kiro](https://open-vsx.org/extension/{PUBLISHER}/umber-calm-kiro) "
            "from Open VSX.\n\n"
            "If you installed an earlier `.vsix` from GitHub, uninstall that Umber Calm first: the extension moved "
            "to this listing, and both are named Umber Calm."),
    },
    "kiro": {
        "title": "Umber Calm for Kiro", "app": "Kiro", "sibling": "VS Code", "hero": "editor",
        "hero_alt": "An editor session in Umber Calm: a Python file with line numbers, one amber cursor and a "
                    "statusline",
        "try": "",
        "install": (
            '1. In Kiro, search for "Umber Calm for Kiro" in the Extensions view and click **Install**.\n'
            "2. Press Cmd/Ctrl+K Cmd/Ctrl+T and choose **Umber Calm**.\n\n"
            "It ships the VS Code theme unchanged. If you imported the VS Code Umber Calm extension into Kiro, "
            "uninstall it first, since both themes are named Umber Calm."),
    },
}


def ratio_text(ratio: float) -> str:
    """One decimal, rounded down so a page never states more contrast than measured; "6.0" reads "6"."""
    text = f"{math.floor(ratio * 10 + EPSILON) / 10:.1f}"
    return text[:-2] if text.endswith(".0") else text


def numbers(pal: Palette, ports) -> dict[str, str]:
    """The page's numbers, defined like the README's: body text rounded down to a whole ratio, the accent range,
    and the ports badge's count (every port that is not archived)."""
    bg = pal.colors["bg"]
    accents = [color.contrast(pal.colors[name], bg) for name in ACCENTS]
    return {"text": str(math.floor(color.contrast(pal.colors["text"], bg) + EPSILON)),
            "accent_min": ratio_text(min(accents)), "accent_max": ratio_text(max(accents)),
            "ports": str(len([p for p in ports if not p.archived_reason]))}


def _slug(pal: Palette) -> str:
    home = pal.meta["homepage"]
    prefix = "https://github.com/"
    if not home.startswith(prefix):
        raise ValueError(f"meta.homepage {home!r} is not a GitHub repository URL")
    return home[len(prefix):].strip("/")


def image_url(pal: Palette, name: str) -> str:
    return f"https://raw.githubusercontent.com/{_slug(pal)}/v{pal.meta['release']}/{IMAGE_DIR}/{name}.png"


def image_names(page_text: str) -> list[str]:
    return list(dict.fromkeys(IMAGE_NAME.findall(page_text)))


def _img(pal: Palette, name: str, width: int, alt: str) -> str:
    return f'<img src="{image_url(pal, name)}" width="{width}" alt="{alt}">'


def page(port_id: str, pal: Palette, ports) -> str:
    if port_id not in PAGES:
        raise ValueError(f"no listing page for port {port_id!r}")
    v, n, home = VARIANTS[port_id], numbers(pal, ports), pal.meta["homepage"]
    head = [f"# {v['title']}", "", "A warm, low-glare dark theme with measured contrast.", ""]
    if v["try"]:
        head += [v["try"], ""]
    body = [
        _img(pal, v["hero"], 760, v["hero_alt"]), "",
        "<sub>Warm near-black background, warm off-white text, and color only where it tells you something.</sub>",
        "",
        "## Why it exists", "",
        "I made Umber Calm for my own eyes. I spend long days in terminals and editors, and most dark themes I tried "
        "felt loud to me: bright white text on pure black, saturated blues, accents all competing for attention. "
        "So I started tuning my own.", "",
        "I used it every day for months, on different machines and at different hours. Whenever something got in "
        "the way, I changed it. When I wasn't sure a color worked, I measured it instead of guessing.", "",
        "What's left is the palette I want to look at all day. I'm sharing it in case it feels that way to you too.",
        "",
        "## What makes it different", "",
        "- **Never pure black, never pure white.** A warm near-black background keeps the screen gently lit, and "
        "warm off-white text stays crisp without glare.",
        f"- **Measured, not eyeballed.** Body text at {n['text']}:1, accents between {n['accent_min']}:1 and "
        f"{n['accent_max']}:1. Every pair is checked automatically on each change.",
        "- **Color with a job.** Red only means errors and deletions. Amber only marks where you are: the cursor and "
        "whatever has focus.",
        "- **Calm by design.** Hues separate keywords, functions, types and strings while lightness stays in a "
        "narrow band, so nothing shouts.", "",
        "## The palette", "",
        _img(pal, "palette", 760, "The Umber Calm palette: seven accents with their roles, above the warm "
                                  "background-to-text ramp"), "",
        f"Every hex value and contrast ratio is in the [palette table on GitHub]({home}#palette).", "",
        "## Checked for color vision", "",
        _img(pal, "color-vision", 760, "The same code in grayscale and as seen with deuteranopia, protanopia and "
                                       "tritanopia"), "",
        "<sub>The same code in grayscale and under deuteranopia, protanopia and tritanopia.</sub>", "",
        "## The same calm everywhere", "",
        f"Umber Calm isn't only a {v['app']} theme. The same palette ships as {n['ports']} ports for editors, "
        f"terminals and tools, so everything you use can match: Neovim, JetBrains IDEs, Zed, {v['sibling']}, "
        "Ghostty, iTerm2, Kitty, WezTerm, Windows Terminal, tmux, Starship and Obsidian.", "",
        _img(pal, "terminal", 372, "A terminal session in Umber Calm") + " "
        + _img(pal, "claude", 372, "A Claude Code session in Umber Calm"), "",
        f"[See every port on GitHub →]({home}#ports)", "",
        "## Install", "",
        v["install"], "",
        "## Feedback", "",
        f"Found a color that gets in the way? [Open an issue]({home}/issues). Umber Calm is MIT-licensed and "
        "maintained in my spare time.",
    ]
    return "\n".join(head + body) + "\n"


def _n(x: float) -> str:
    return f"{round(x, 2):g}"


def icon_svg(pal: Palette) -> str:
    """Four code lines and one amber cursor on the background: amber marks where you are, as everywhere else."""
    c = pal.colors
    lines = ((60, 112, "yellow"), (100, 156, "blue"), (140, 92, "green"), (180, 128, "dim_text"))
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">',
           f'<rect width="256" height="256" rx="44" fill="{c["bg"]}"/>']
    out += [f'<rect x="44" y="{y}" width="{w}" height="18" rx="9" fill="{c[name]}"/>' for y, w, name in lines]
    out += [f'<rect x="184" y="176" width="10" height="28" rx="2" fill="{c["orange"]}"/>', "</svg>"]
    return "\n".join(out) + "\n"


def palette_svg(pal: Palette) -> str:
    """The seven accents with their roles above the background-to-text ramp, on the background."""
    c = pal.colors
    tile = (STRIP_W - 2 * PAD - GAP * (len(STRIP_ORDER) - 1)) / len(STRIP_ORDER)
    seg = (STRIP_W - 2 * PAD - GAP * (len(RAMP) - 1)) / len(RAMP)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{STRIP_W}" height="{STRIP_H}" '
           f'viewBox="0 0 {STRIP_W} {STRIP_H}" font-family="{MONO}" font-size="12" text-anchor="middle">',
           f'<rect width="{STRIP_W}" height="{STRIP_H}" rx="12" fill="{c["bg"]}"/>']
    for i, (name, role) in enumerate(STRIP_ORDER):
        x = PAD + i * (tile + GAP)
        cx = _n(x + tile / 2)
        out += [f'<rect x="{_n(x)}" y="{PAD}" width="{_n(tile)}" height="44" rx="6" fill="{c[name]}"/>',
                f'<text x="{cx}" y="76" fill="{c["text"]}">{name}</text>',
                f'<text x="{cx}" y="92" fill="{c["muted"]}">{role}</text>']
    for i, name in enumerate(RAMP):
        x = PAD + i * (seg + GAP)
        out.append(f'<rect x="{_n(x)}" y="112" width="{_n(seg)}" height="40" rx="5" fill="{c[name]}" '
                   f'stroke="{c["overlay"]}"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def source_digest(root: Path, name: str) -> str:
    return "sha256:" + hashlib.sha256(safepath.read_bytes(root, IMAGES[name])).hexdigest()


def png_size(data: bytes) -> tuple[int, int] | None:
    """Width and height from a PNG's IHDR chunk, or None when the bytes are not a PNG."""
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def _sources(root: Path) -> dict | None:
    """The recorded source digests ({} before any image is made), or None when the file is not a JSON object."""
    path = root / SOURCES
    if not path.is_file():
        return {}
    try:
        sources = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:  # bad JSON or bad UTF-8
        return None
    return sources if isinstance(sources, dict) else None


def image_problems(root: Path) -> list[str]:
    """The committed PNGs must cover every image a page links, and each must still match the source it was made
    from: the PNGs are not regenerated by the build, so a palette or theme change would otherwise ship old images."""
    root = Path(root)
    found = []
    for rel in PAGES.values():
        page_path = root / rel
        if not page_path.is_file():
            continue
        for name in image_names(page_path.read_text(encoding="utf-8")):
            if not (root / IMAGE_DIR / f"{name}.png").is_file():
                found.append(f"marketplace: {rel} links {IMAGE_DIR}/{name}.png, which does not exist")
    sources = _sources(root)
    if sources is None:
        found.append(f"marketplace: {SOURCES} is not a JSON object of image digests (run tools/marketplace_images.py)")
        sources = {}
    icon = root / IMAGE_DIR / "icon.png"
    if icon.is_file():
        size = png_size(icon.read_bytes())
        if size is None or min(size) < ICON_MIN:
            shape = "not a PNG" if size is None else f"{size[0]}x{size[1]}"
            found.append(f"marketplace: {IMAGE_DIR}/icon.png must be a PNG of at least {ICON_MIN}x{ICON_MIN} pixels "
                         f"(it is {shape})")
    for png in sorted((root / IMAGE_DIR).glob("*.png")):
        name, rel = png.stem, f"{IMAGE_DIR}/{png.name}"
        if name not in IMAGES:
            found.append(f"marketplace: {rel} is not a listed marketplace image")
        elif name not in sources:
            found.append(f"marketplace: {rel} has no entry in {SOURCES}")
        elif not (root / IMAGES[name]).is_file() or sources[name] != source_digest(root, name):
            found.append(f"marketplace: {rel} is stale: {IMAGES[name]} changed since it was made "
                         "(run tools/marketplace_images.py)")
    return found


def plan(pal: Palette, ports) -> dict[str, tuple[str, bytes]]:
    """The listing pages and the SVG sources of their icon and palette strip, under the owner "docs"."""
    out = {rel: (OWNER, page(pid, pal, ports).encode("utf-8")) for pid, rel in PAGES.items()}
    out["docs/marketplace/icon.svg"] = (OWNER, icon_svg(pal).encode("utf-8"))
    out["docs/marketplace/palette.svg"] = (OWNER, palette_svg(pal).encode("utf-8"))
    return out
