#!/usr/bin/env python3
"""Build every release artifact into dist/ (run tools/build.py first)."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from umber import REPO_ROOT  # noqa: E402
from umber.package import PackageError, package  # noqa: E402
from umber.safepath import UnsafePathError  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="package.py", description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "dist")
    args = parser.parse_args(argv)
    try:
        for path in package(REPO_ROOT, args.out.resolve()):
            print(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)
    except (PackageError, UnsafePathError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
