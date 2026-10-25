#!/usr/bin/env python3
"""Make the listing PNGs in assets/marketplace/ from their SVG sources, or record a screenshot's source.

Maintainer-only: needs rsvg-convert (brew install librsvg). Strip PNG metadata and look at every image before
committing. `record` is for images made by hand (the VS Code screenshot): it stores the digest of the file the
image depends on, so check.py reports the image as stale when that file changes.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from umber import REPO_ROOT  # noqa: E402
from umber.marketplace import IMAGE_DIR, IMAGES, SOURCES, source_digest  # noqa: E402

SVG_IMAGES = [name for name, src in IMAGES.items() if src.endswith(".svg")]


def _record(names: list[str]) -> None:
    path = REPO_ROOT / SOURCES
    sources = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    sources.update({name: source_digest(REPO_ROOT, name) for name in names})
    path.write_text(json.dumps(sources, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render(names: list[str]) -> int:
    tool = shutil.which("rsvg-convert")
    if not tool:
        print("rsvg-convert not found: brew install librsvg", file=sys.stderr)
        return 1
    (REPO_ROOT / IMAGE_DIR).mkdir(parents=True, exist_ok=True)
    for name in names:
        size = ["--width", "256", "--height", "256"] if name == "icon" else ["--zoom", "2"]
        target = REPO_ROOT / IMAGE_DIR / f"{name}.png"
        subprocess.run([tool, *size, "--output", str(target), str(REPO_ROOT / IMAGES[name])], check=True)
        print(target.relative_to(REPO_ROOT))
    _record(names)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="marketplace_images.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("render", help="render the SVG-sourced images (all of them when no name is given)")
    r.add_argument("names", nargs="*", metavar="NAME")
    c = sub.add_parser("record", help="record the source digest of an image made by hand")
    c.add_argument("name", metavar="NAME")
    args = parser.parse_args(argv)
    if args.command == "render":
        names = args.names or SVG_IMAGES
        bad = [n for n in names if n not in SVG_IMAGES]
        if bad:
            print(f"not an SVG-sourced image: {', '.join(bad)} (choose from {', '.join(SVG_IMAGES)})", file=sys.stderr)
            return 1
        return _render(names)
    if args.name not in IMAGES:
        print(f"unknown image {args.name!r} (choose from {', '.join(IMAGES)})", file=sys.stderr)
        return 1
    _record([args.name])
    return 0


if __name__ == "__main__":
    sys.exit(main())
