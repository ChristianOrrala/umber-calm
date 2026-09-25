#!/usr/bin/env python3
"""Check that the current commit may be released as the given tag (spec §14). Exit 1 on any problem."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from umber import REPO_ROOT  # noqa: E402
from umber.release import gate  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="release_gate.py", description=__doc__)
    parser.add_argument("--tag", required=True, help="the tag being released, e.g. v0.1.0")
    args = parser.parse_args(argv)
    problems = gate(REPO_ROOT, args.tag)
    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s)" if problems else f"release gate passed for {args.tag}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
