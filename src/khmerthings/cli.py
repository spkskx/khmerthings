"""Command-line interface: ``khmerthings <tool> ...``.

Each library tool is a subcommand; new tools register a subparser here.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import subprocess
import sys
from collections.abc import Sequence

from khmerthings import __version__
from khmerthings.counter import analyze
from khmerthings.lexicon import WORD_SOURCES, Lexicon, load_lexicon
from khmerthings.normalize import normalize_text, space_sentences, space_words
from khmerthings.segmenter import break_words, mark_boundaries
from khmerthings.spellcheck import fix_spelling

__all__ = ["main"]


def _read_source(path: str) -> tuple[str, str]:
    """Return (source label, text) for a file path or '-' for stdin."""
    if path == "-":
        return "<stdin>", sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return path, f.read()


def _lexicon_from_args(args: argparse.Namespace) -> Lexicon:
    includes = tuple(s.strip() for s in (args.include or "").split(",") if s.strip())
    return load_lexicon("words", *includes)


def _add_include_option(parser: argparse.ArgumentParser) -> None:
    extra = sorted(set(WORD_SOURCES) - {"words"})
    parser.add_argument(
        "--include",
        metavar=",".join(extra),
        help=f"extra wordlists to match against, comma-separated (available: {', '.join(extra)})",
    )


def _cmd_count(args: argparse.Namespace) -> int:
    paths: list[str] = args.files or ["-"]
    lexicon = _lexicon_from_args(args)
    results = []
    for path in paths:
        source, text = _read_source(path)
        results.append({"source": source, **dataclasses.asdict(analyze(text, lexicon))})

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    for result in results:
        if len(results) > 1:
            print(f"{result['source']}:")
        for field in dataclasses.fields(analyze("")):
            print(f"  {field.name}: {result[field.name]}")
    return 0


def _cmd_segment(args: argparse.Namespace) -> int:
    paths: list[str] = args.files or ["-"]
    lexicon = _lexicon_from_args(args)
    if args.mark:
        separator = args.separator if args.separator is not None else "​"
    else:
        separator = args.separator if args.separator is not None else " "
    for path in paths:
        _, text = _read_source(path)
        for line in text.splitlines():
            if args.mark:
                print(mark_boundaries(line, separator, lexicon))
            else:
                print(separator.join(break_words(line, lexicon)))
    return 0


def _normalized(args: argparse.Namespace, lexicon: Lexicon, line: str) -> str:
    if args.only == "words":
        return space_words(fix_spelling(line, lexicon), lexicon)
    if args.only == "sentences":
        return space_sentences(line)
    return normalize_text(line, lexicon)


def _cmd_normalize(args: argparse.Namespace) -> int:
    paths: list[str] = args.files or ["-"]
    lexicon = _lexicon_from_args(args)
    for path in paths:
        _, text = _read_source(path)
        for line in text.splitlines():
            print(_normalized(args, lexicon, line))
    return 0


def _package_command(action: str) -> list[str]:
    executable = sys.executable.replace("\\", "/")
    if "/uv/tools/khmerthings/" in executable:
        uv_action = "upgrade" if action == "update" else "uninstall"
        return ["uv", "tool", uv_action, "khmerthings"]
    if "/pipx/venvs/khmerthings/" in executable:
        pipx_action = "upgrade" if action == "update" else "uninstall"
        return ["pipx", pipx_action, "khmerthings"]
    if action == "update":
        return [sys.executable, "-m", "pip", "install", "--upgrade", "khmerthings"]
    return [sys.executable, "-m", "pip", "uninstall", "-y", "khmerthings"]


def _cmd_update(args: argparse.Namespace) -> int:
    del args
    command = _package_command("update")
    print(f"Updating khmerthings with {command[0]}...")
    return subprocess.run(command, check=False).returncode


def _cmd_uninstall(args: argparse.Namespace) -> int:
    del args
    answer = input("Uninstall khmerthings? [y/N] ").strip().lower()
    if answer not in {"y", "yes"}:
        print("Uninstall cancelled.")
        return 0
    command = _package_command("uninstall")
    print(f"Uninstalling khmerthings with {command[0]}...")
    return subprocess.run(command, check=False).returncode


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
    _add_include_option(count)
    count.set_defaults(func=_cmd_count)

    segment = subparsers.add_parser(
        "segment", help="break Khmer text into words (word segmentation)"
    )
    segment.add_argument("files", nargs="*", help="input files, or '-' for stdin (default)")
    segment.add_argument(
        "--separator",
        help="word separator (default: space, or ZWSP with --mark)",
    )
    segment.add_argument(
        "--mark",
        action="store_true",
        help="preserve the line as-is and only insert separators at Khmer word boundaries",
    )
    _add_include_option(segment)
    segment.set_defaults(func=_cmd_segment)

    normalize = subparsers.add_parser(
        "normalize", help="spellfix and re-space text into clean, ready-to-use form"
    )
    normalize.add_argument("files", nargs="*", help="input files, or '-' for stdin (default)")
    normalize.add_argument(
        "--only",
        choices=["words", "sentences"],
        help="apply only one pass: words (spellfix + hidden-space + whitespace collapse) "
        "or sentences (Khmer sentence-stop spacing, lexicon-free); default: both",
    )
    _add_include_option(normalize)
    normalize.set_defaults(func=_cmd_normalize)

    update = subparsers.add_parser("update", help="update khmerthings to the latest version")
    update.set_defaults(func=_cmd_update)

    uninstall = subparsers.add_parser("uninstall", help="uninstall khmerthings after confirmation")
    uninstall.set_defaults(func=_cmd_uninstall)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result: int = args.func(args)
    except ValueError as exc:  # e.g. unknown --include source
        parser.error(str(exc))
    except OSError as exc:  # e.g. missing or unreadable input file
        print(f"khmerthings: error: {exc}", file=sys.stderr)
        return 1
    return result


if __name__ == "__main__":
    sys.exit(main())
