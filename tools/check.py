#!/usr/bin/env python3
"""Run every repository check; exit 1 if any problem is found."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from umber import REPO_ROOT  # noqa: E402
from umber.checks import run  # noqa: E402


def main() -> int:
    problems = run(REPO_ROOT)
    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s)" if problems else "all checks passed")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
