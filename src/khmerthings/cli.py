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
from khmerthings.condense import DEFAULT_REMOVE, condense_text, content_words
from khmerthings.counter import analyze
from khmerthings.lexicon import STOPWORD_CATEGORIES, WORD_SOURCES, Lexicon, load_lexicon
from khmerthings.normalize import normalize_text
from khmerthings.segmenter import break_words, mark_boundaries
from khmerthings.sorting import sort_lines
from khmerthings.spellcheck import check_spelling, fix_spelling

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


def _cmd_sort(args: argparse.Namespace) -> int:
    paths: list[str] = args.files or ["-"]
    lines: list[str] = []
    for path in paths:
        _, text = _read_source(path)
        lines.extend(text.splitlines())
    for line in sort_lines(lines, descending=args.desc):
        print(line)
    return 0


def _cmd_spellcheck(args: argparse.Namespace) -> int:
    paths: list[str] = args.files or ["-"]
    lexicon = _lexicon_from_args(args)
    json_issues: list[dict[str, object]] = []
    found = False
    for path in paths:
        source, text = _read_source(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            for issue in check_spelling(line, lexicon, max_suggestions=args.max_suggestions):
                found = True
                if args.json:
                    json_issues.append(
                        {
                            "source": source,
                            "line": lineno,
                            "col": issue.start + 1,
                            "start": issue.start,
                            "end": issue.end,
                            "text": issue.text,
                            "kind": issue.kind.value,
                            "suggestions": list(issue.suggestions),
                        }
                    )
                else:
                    location = f"{source}:{lineno}:{issue.start + 1}"
                    message = f"{location}: {issue.kind.value}: {issue.text}"
                    if issue.suggestions:
                        message += " -> " + ", ".join(issue.suggestions)
                    print(message)
    if args.json:
        print(json.dumps(json_issues, ensure_ascii=False, indent=2))
    return 1 if found else 0


def _cmd_spellfix(args: argparse.Namespace) -> int:
    paths: list[str] = args.files or ["-"]
    lexicon = _lexicon_from_args(args)
    for path in paths:
        _, text = _read_source(path)
        for line in text.splitlines():
            print(fix_spelling(line, lexicon))
    return 0


def _cmd_normalize(args: argparse.Namespace) -> int:
    paths: list[str] = args.files or ["-"]
    lexicon = _lexicon_from_args(args)
    for path in paths:
        _, text = _read_source(path)
        for line in text.splitlines():
            print(normalize_text(line, lexicon))
    return 0


def _cmd_condense(args: argparse.Namespace) -> int:
    paths: list[str] = args.files or ["-"]
    lexicon = _lexicon_from_args(args)
    if args.remove is not None:
        remove = frozenset(s.strip() for s in args.remove.split(",") if s.strip())
    else:
        remove = DEFAULT_REMOVE
    for path in paths:
        _, text = _read_source(path)
        for line in text.splitlines():
            if args.words:
                for word in content_words(line, lexicon, remove=remove):
                    print(word)
            else:
                print(condense_text(line, lexicon, remove=remove))
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

    spellcheck = subparsers.add_parser(
        "spellcheck", help="report misspellings and unknown Khmer words"
    )
    spellcheck.add_argument("files", nargs="*", help="input files, or '-' for stdin (default)")
    spellcheck.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    spellcheck.add_argument(
        "--max-suggestions",
        type=int,
        default=3,
        metavar="N",
        help="maximum suggestions per unknown word (default: 3)",
    )
    _add_include_option(spellcheck)
    spellcheck.set_defaults(func=_cmd_spellcheck)

    spellfix = subparsers.add_parser(
        "spellfix", help="rewrite known misspellings to their canonical spelling"
    )
    spellfix.add_argument("files", nargs="*", help="input files, or '-' for stdin (default)")
    _add_include_option(spellfix)
    spellfix.set_defaults(func=_cmd_spellfix)

    normalize = subparsers.add_parser(
        "normalize", help="spellfix and re-space text into clean, ready-to-use form"
    )
    normalize.add_argument("files", nargs="*", help="input files, or '-' for stdin (default)")
    _add_include_option(normalize)
    normalize.set_defaults(func=_cmd_normalize)

    condense = subparsers.add_parser(
        "condense",
        help="strip function words, keeping only content (meaning-bearing) words",
    )
    condense.add_argument("files", nargs="*", help="input files, or '-' for stdin (default)")
    condense.add_argument(
        "--remove",
        metavar="CAT,CAT",
        help=(
            "stopword categories to strip, comma-separated (default: "
            + ",".join(sorted(DEFAULT_REMOVE))
            + "; all: "
            + ",".join(sorted(STOPWORD_CATEGORIES))
            + ")"
        ),
    )
    condense.add_argument(
        "--words",
        action="store_true",
        help="output one content word per line instead of the condensed line",
    )
    _add_include_option(condense)
    condense.set_defaults(func=_cmd_condense)

    sort = subparsers.add_parser(
        "sort", help="sort lines in Khmer dictionary order (ascending by default)"
    )
    sort.add_argument("files", nargs="*", help="input files, or '-' for stdin (default)")
    sort.add_argument("--desc", action="store_true", help="sort in descending order")
    sort.set_defaults(func=_cmd_sort)

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
