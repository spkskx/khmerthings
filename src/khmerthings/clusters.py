"""Khmer character-cluster (KCC) segmentation.

A Khmer character cluster is the smallest user-visible unit of text: a base
consonant or independent vowel, optionally followed by subscript (coeng)
consonants, dependent vowels, and combining signs. Cluster boundaries are the
only positions where a word boundary can legally occur, which makes this the
foundation for word segmentation.

The segmenter is a deterministic scanner over NFC-normalized text. It never
drops or reorders characters: ``"".join(segment_clusters(t))`` always equals
``unicodedata.normalize("NFC", t)``. Malformed sequences (orphan coeng,
orphan vowel) are attached to the preceding cluster when one exists,
otherwise emitted as standalone clusters.
"""

from __future__ import annotations

import unicodedata

from khmerthings.chars import (
    is_coeng as _is_coeng,
)
from khmerthings.chars import (
    is_consonant,
    is_dependent_vowel,
    is_independent_vowel,
    is_inherent_vowel,
    is_khmer,
    is_sign,
)

__all__ = ["segment_clusters"]


def _is_base(ch: str) -> bool:
    return is_consonant(ch) or is_independent_vowel(ch)


def _is_trailing(ch: str) -> bool:
    """Characters that extend the current cluster (excluding coeng pairs)."""
    return is_dependent_vowel(ch) or is_sign(ch) or is_inherent_vowel(ch)


def segment_clusters(text: str) -> list[str]:
    """Split *text* into Khmer character clusters.

    Non-Khmer characters are emitted as single-character clusters. The input
    is NFC-normalized first; the concatenation of the result equals the
    normalized input.
    """
    text = unicodedata.normalize("NFC", text)
    clusters: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if _is_base(ch):
            j = i + 1
            while j < n:
                c = text[j]
                if _is_coeng(c) and j + 1 < n and _is_base(text[j + 1]):
                    j += 2
                elif _is_trailing(c):
                    j += 1
                else:
                    break
            clusters.append(text[i:j])
            i = j
        elif (_is_trailing(ch) or _is_coeng(ch)) and clusters and is_khmer(clusters[-1][-1]):
            # Orphan combining mark: attach to the preceding Khmer cluster.
            clusters[-1] += ch
            i += 1
        else:
            # Digits, symbols, punctuation, non-Khmer, or leading orphan marks.
            clusters.append(ch)
            i += 1
    return clusters
