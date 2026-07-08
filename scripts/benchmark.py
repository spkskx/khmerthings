#!/usr/bin/env python3
"""Micro-benchmark the deterministic hot paths.

A development aid, not a test. It times the three code paths most likely to
dominate on large inputs:

1. cluster segmentation (``segment_clusters``) — the base primitive;
2. trie longest-match tokenization (``tokenize``) — the segmentation core;
3. edit-distance spell checking (``check_unknown``) — the one super-linear path.

It builds a synthetic corpus by repeating a fixed sample so results are
reproducible and depend on no external text. Run::

    python scripts/benchmark.py            # default size
    python scripts/benchmark.py --repeat 4000

Optimize only if a path here is demonstrably slow; keep this script as the
before/after guard for any such change.
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable

from khmerthings.clusters import segment_clusters
from khmerthings.spellcheck import check_unknown
from khmerthings.tokenizer import tokenize

# A mixed sample: known words, an unknown span, digits, Latin, punctuation.
_SAMPLE = "ខ្ញុំចង់ទៅផ្សារនៅថ្ងៃស្អែក ការសិក្សានិងការងារ hello ២០២៦ ក្ស្ក។ "


def _time(label: str, fn: Callable[[], object], rounds: int = 3) -> None:
    best = min(_once(fn) for _ in range(rounds))
    print(f"  {label:<28} {best * 1000:8.1f} ms")


def _once(fn: Callable[[], object]) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repeat", type=int, default=2000, help="sample repetitions")
    args = parser.parse_args(argv)

    corpus = _SAMPLE * args.repeat
    chars = len(corpus)
    print(f"corpus: {chars:,} characters ({args.repeat} reps)")

    # Warm the lexicon/data caches so we time the algorithm, not the load.
    tokenize("ក")
    check_unknown("ក")

    _time("segment_clusters", lambda: segment_clusters(corpus))
    _time("tokenize (longest-match)", lambda: tokenize(corpus))
    # check_unknown is super-linear; run it on a smaller slice.
    small = _SAMPLE * min(args.repeat, 200)
    _time(f"check_unknown ({len(small):,} ch)", lambda: check_unknown(small))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
