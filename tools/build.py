#!/usr/bin/env python3
"""Render every port and refresh README sections; print a port's digest; or record a verification."""
import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from umber import REPO_ROOT  # noqa: E402
from umber.buildcmd import CommandError, build, mark, port_digest  # noqa: E402
from umber.outputs import BuildError  # noqa: E402
from umber.palette import PaletteError  # noqa: E402
from umber.readme import ReadmeError  # noqa: E402
from umber.registry import OS_NAMES, RegistryError  # noqa: E402
from umber.safepath import UnsafePathError  # noqa: E402
from umber.template import TemplateError  # noqa: E402

ERRORS = (CommandError, BuildError, PaletteError, ReadmeError, RegistryError, TemplateError, UnsafePathError)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="build.py", description=__doc__)
    sub = parser.add_subparsers(dest="command")
    d = sub.add_parser("digest", help="print a port's full current digest and the files it covers")
    d.add_argument("port")
    m = sub.add_parser("mark", help="record a verification of the exact files you tested")
    m.add_argument("port")
    m.add_argument("status", choices=["verified", "needs-fix"])
    m.add_argument("--digest", required=True, help="the full sha256:… printed by `build.py digest <port>` before testing")
    m.add_argument("--app-version", required=True, help="digits and dots, e.g. 0.39.1 (a leading v is dropped)")
    m.add_argument("--os", required=True, dest="os_name", choices=OS_NAMES)
    m.add_argument("--os-version", default="", help="digits and dots, e.g. 15.1")
    m.add_argument("--note", default="", help="one line, at most 200 characters")
    m.add_argument("--evidence", default="", help="URL of this repository's issue, pull request or discussion")
    args = parser.parse_args(argv)
    try:
        if args.command == "digest":
            value, files = port_digest(REPO_ROOT, args.port)
            print(value)
            print("\n".join(files))
        elif args.command == "mark":
            record = mark(REPO_ROOT, args.port, args.status, digest=args.digest, app_version=args.app_version,
                          os_name=args.os_name, os_version=args.os_version, note=args.note,
                          evidence=args.evidence, today=datetime.date.today().isoformat())
            print(f"recorded {args.status} for {args.port} ({record['digest']})")
        else:
            changed = build(REPO_ROOT)
            print("\n".join(changed) if changed else "up to date")
    except ERRORS as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
