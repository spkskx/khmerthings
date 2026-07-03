"""Khmer-aware line sorting.

Plain codepoint sorting gets Khmer dictionary order wrong: the coeng sign
(U+17D2) has a higher codepoint than every dependent vowel, so ``ក្រ`` would
sort after ``កៅ`` cluster-internally in some cases and, worse, a subscript
consonant would compare by the coeng codepoint rather than grouping with its
base. Khmer dictionaries order entries per character cluster: first by base
consonant, then subscript consonants, then dependent vowels, then signs.

``khmer_sort_key`` implements that as a deterministic collation key built on
:func:`khmerthings.clusters.segment_clusters`: each cluster contributes a
``(base, coengs, vowels, signs)`` tuple of codepoints, and the NFC-normalized
string is appended as a final tiebreaker so the ordering is total. Non-Khmer
characters form single-character clusters keyed by their codepoint, so ASCII
sorts before Khmer text.

This is a practical approximation of Khmer dictionary (Chuon Nath) order,
not a full CLDR collation.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable

from khmerthings.chars import (
    is_coeng,
    is_dependent_vowel,
    is_inherent_vowel,
)
from khmerthings.clusters import segment_clusters

__all__ = ["khmer_sort_key", "sort_lines"]

ClusterKey = tuple[int, tuple[int, ...], tuple[int, ...], tuple[int, ...]]
SortKey = tuple[tuple[ClusterKey, ...], str]


def _cluster_key(cluster: str) -> ClusterKey:
    base = 0
    coengs: list[int] = []
    vowels: list[int] = []
    signs: list[int] = []
    i = 0
    while i < len(cluster):
        ch = cluster[i]
        if is_coeng(ch) and i + 1 < len(cluster):
            coengs.append(ord(cluster[i + 1]))
            i += 2
        elif is_dependent_vowel(ch) or is_inherent_vowel(ch):
            vowels.append(ord(ch))
            i += 1
        elif i == 0:
            base = ord(ch)
            i += 1
        else:
            # Signs, and any malformed trailing character (e.g. orphan coeng).
            signs.append(ord(ch))
            i += 1
    return (base, tuple(coengs), tuple(vowels), tuple(signs))


def khmer_sort_key(text: str) -> SortKey:
    """Collation key for *text* approximating Khmer dictionary order.

    Usable directly as a ``sorted(..., key=khmer_sort_key)`` key for any
    string; non-Khmer text falls back to codepoint order.
    """
    text = unicodedata.normalize("NFC", text)
    return (tuple(_cluster_key(c) for c in segment_clusters(text)), text)


def sort_lines(lines: Iterable[str], *, descending: bool = False) -> list[str]:
    """Sort *lines* in Khmer dictionary order (ascending by default).

    Duplicates are kept. The ordering is deterministic and total: lines with
    identical collation keys are ordered by their NFC-normalized text.
    """
    return sorted(lines, key=khmer_sort_key, reverse=descending)
