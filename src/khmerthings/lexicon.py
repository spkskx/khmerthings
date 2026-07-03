"""Khmer word lexicon with longest-match lookup.

The lexicon is a trie keyed by character clusters (not codepoints), so a
match can never end in the middle of a cluster. ``longest_match`` is the
core primitive for greedy word segmentation and, later, the word breaker.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Iterator, Sequence
from functools import cache
from importlib import resources

from khmerthings.chars import ZERO_WIDTH_SPACE, is_khmer_letter_or_mark
from khmerthings.clusters import segment_clusters

__all__ = ["Lexicon", "default_lexicon"]

_END = "\x00"  # trie sentinel; cannot collide with any cluster


class Lexicon:
    """An immutable set of Khmer words supporting longest-match lookup."""

    def __init__(self, words: Iterable[str]) -> None:
        self._words: set[str] = set()
        self._trie: dict[str, object] = {}
        for word in words:
            self._add(word)

    def _add(self, word: str) -> None:
        if not word:
            raise ValueError("empty word")
        if unicodedata.normalize("NFC", word) != word:
            raise ValueError(f"word is not NFC-normalized: {word!r}")
        if not all(is_khmer_letter_or_mark(ch) for ch in word):
            raise ValueError(f"word contains non-Khmer characters: {word!r}")
        if word in self._words:
            raise ValueError(f"duplicate word: {word!r}")
        self._words.add(word)
        node = self._trie
        for cluster in segment_clusters(word):
            node = node.setdefault(cluster, {})  # type: ignore[assignment]
        node[_END] = True

    @classmethod
    def from_lines(cls, lines: Iterable[str]) -> Lexicon:
        """Build a lexicon from wordlist lines.

        Blank lines and lines starting with ``#`` are ignored; other lines
        are stripped of surrounding whitespace (including ZWSP).
        """
        words = []
        for line in lines:
            word = line.strip().strip(ZERO_WIDTH_SPACE)
            if word and not word.startswith("#"):
                words.append(word)
        return cls(words)

    def __contains__(self, word: str) -> bool:
        return word in self._words

    def __len__(self) -> int:
        return len(self._words)

    def __iter__(self) -> Iterator[str]:
        return iter(sorted(self._words))

    def longest_match(self, clusters: Sequence[str], start: int = 0) -> int:
        """Length in clusters of the longest word starting at *start*.

        Returns 0 if no word in the lexicon matches there.
        """
        node = self._trie
        best = 0
        for i in range(start, len(clusters)):
            next_node = node.get(clusters[i])
            if next_node is None:
                break
            node = next_node  # type: ignore[assignment]
            if _END in node:
                best = i - start + 1
        return best


@cache
def default_lexicon() -> Lexicon:
    """The built-in seed lexicon shipped with the package."""
    text = (resources.files("khmerthings") / "data" / "words.txt").read_text("utf-8")
    return Lexicon.from_lines(text.splitlines())
