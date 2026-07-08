#!/usr/bin/env python3
"""Report the Khmer words the lexicon does not yet know.

A development aid for growing the wordlists: it runs text through the
tokenizer with the full merged lexicon (``words`` + ``names`` + ``modern``)
and lists every ``KHMER_UNKNOWN`` span — the runs of Khmer clusters that
greedy longest-match could not resolve to a known word — ranked by how often
they occur. Each line is a candidate for hand-curation into ``words.txt``
(after individual verification; see AGENTS.md).

This is a *dev-only* tool. It ships no corpus and reads whatever text you
give it, so nothing about how candidates were found is recorded in the repo.

Usage::

    python scripts/coverage_gaps.py path/to/text.txt [more.txt ...]
    cat corpus.txt | python scripts/coverage_gaps.py
    python scripts/coverage_gaps.py --min-count 3 corpus.txt

Exit status is 0 regardless of findings; this reports, it does not gate.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from khmerthings.clusters import segment_clusters
from khmerthings.lexicon import load_lexicon
from khmerthings.tokenizer import TokenType, tokenize


def collect_gaps(text: str) -> tuple[Counter[str], int]:
    """Return (unknown-span → count, total Khmer-word token count) for *text*.

    "Khmer-word tokens" counts both resolved words and unknown spans, so the
    ratio of unknown to total is a coverage figure for the given text.
    """
    lexicon = load_lexicon("words", "names", "modern")
    unknown: Counter[str] = Counter()
    khmer_words = 0
    for token in tokenize(text, lexicon):
        if token.type is TokenType.KHMER_UNKNOWN:
            unknown[token.text] += 1
            khmer_words += 1
        elif token.type is TokenType.KHMER_WORD:
            khmer_words += 1
    return unknown, khmer_words


def format_report(unknown: Counter[str], khmer_words: int, min_count: int) -> str:
    lines: list[str] = []
    shown = [(span, n) for span, n in unknown.most_common() if n >= min_count]
    total_unknown = sum(unknown.values())
    coverage = 100.0 * (khmer_words - total_unknown) / khmer_words if khmer_words else 100.0
    lines.append(
        f"# {khmer_words} Khmer-word tokens, {total_unknown} unknown "
        f"({len(unknown)} distinct), coverage {coverage:.1f}%"
    )
    if not shown:
        lines.append("# no unknown spans at or above the count threshold")
        return "\n".join(lines)
    lines.append("# count  span  (clusters)")
    for span, n in shown:
        clusters = " ".join(segment_clusters(span))
        lines.append(f"{n:>6}  {span}  ({clusters})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", help="text files to scan (default: stdin)")
    parser.add_argument(
        "--min-count",
        type=int,
        default=1,
        help="only report spans occurring at least this many times (default: 1)",
    )
    args = parser.parse_args(argv)

    if args.files:
        text = "\n".join(Path(path).read_text(encoding="utf-8") for path in args.files)
    else:
        text = sys.stdin.read()

    unknown, khmer_words = collect_gaps(text)
    print(format_report(unknown, khmer_words, args.min_count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
