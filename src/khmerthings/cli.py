"""Command-line interface: ``khmerthings <tool> ...``.

Each library tool is a subcommand; new tools register a subparser here.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from collections.abc import Sequence

from khmerthings import __version__
from khmerthings.counter import analyze
from khmerthings.sorting import sort_lines

__all__ = ["main"]


def _read_source(path: str) -> tuple[str, str]:
    """Return (source label, text) for a file path or '-' for stdin."""
    if path == "-":
        return "<stdin>", sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return path, f.read()


def _cmd_count(args: argparse.Namespace) -> int:
    paths: list[str] = args.files or ["-"]
    results = []
    for path in paths:
        source, text = _read_source(path)
        results.append({"source": source, **dataclasses.asdict(analyze(text))})

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    for result in results:
        if len(results) > 1:
            print(f"{result['source']}:")
        for field in dataclasses.fields(analyze("")):
            print(f"  {field.name}: {result[field.name]}")
    return 0


def _cmd_sort(args: argparse.Namespace) -> int:
    paths: list[str] = args.files or ["-"]
    lines: list[str] = []
    for path in paths:
        _, text = _read_source(path)
        lines.extend(text.splitlines())
    for line in sort_lines(lines, descending=args.desc):
        print(line)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="khmerthings",
        description="Deterministic Khmer language tools.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    count = subparsers.add_parser("count", help="count words in Khmer (or mixed) text")
    count.add_argument("files", nargs="*", help="input files, or '-' for stdin (default)")
    count.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    count.set_defaults(func=_cmd_count)

    sort = subparsers.add_parser(
        "sort", help="sort lines in Khmer dictionary order (ascending by default)"
    )
    sort.add_argument("files", nargs="*", help="input files, or '-' for stdin (default)")
    sort.add_argument("--desc", action="store_true", help="sort in descending order")
    sort.set_defaults(func=_cmd_sort)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
