#!/usr/bin/env python3
"""Markpact CLI"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .parser import parse_blocks
from .runner import install_deps, run_cmd
from .sandbox import Sandbox


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="markpact",
        description="Executable Markdown Runtime – run projects from README.md",
    )
    parser.add_argument("readme", nargs="?", default="README.md", help="Path to README.md")
    parser.add_argument("--sandbox", "-s", help="Sandbox directory (default: ./sandbox)")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be done")
    parser.add_argument("--version", "-V", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")

    args = parser.parse_args(argv)
    readme = Path(args.readme)

    if not readme.exists():
        print(f"[markpact] ERROR: {readme} not found", file=sys.stderr)
        return 1

    sandbox = Sandbox(args.sandbox)
    verbose = not args.quiet

    if verbose:
        print(f"[markpact] Parsing {readme}")

    blocks = parse_blocks(readme.read_text())
    deps: list[str] = []
    run_command: str | None = None

    for block in blocks:
        if block.kind == "bootstrap":
            continue  # skip bootstrap itself

        if block.kind == "file":
            path = block.get_path()
            if not path:
                print(f"[markpact] ERROR: markpact:file requires path=..., got: {block.meta}", file=sys.stderr)
                return 1
            if args.dry_run:
                print(f"[markpact] Would write {sandbox.path / path}")
            else:
                f = sandbox.write_file(path, block.body)
                if verbose:
                    print(f"[markpact] wrote {f}")

        elif block.kind == "deps" and "python" in block.meta:
            deps.extend(line.strip() for line in block.body.splitlines() if line.strip())

        elif block.kind == "run":
            run_command = block.body

    if deps:
        if args.dry_run:
            print(f"[markpact] Would install: {', '.join(deps)}")
        else:
            install_deps(deps, sandbox, verbose)

    if run_command:
        if args.dry_run:
            print(f"[markpact] Would run: {run_command}")
        else:
            run_cmd(run_command, sandbox, verbose)
    elif verbose:
        print("[markpact] No run command defined")

    return 0


if __name__ == "__main__":
    sys.exit(main())
