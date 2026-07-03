"""Khmer-aware word counting."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from khmerthings.chars import is_khmer
from khmerthings.clusters import segment_clusters
from khmerthings.lexicon import Lexicon
from khmerthings.tokenizer import TokenType, tokenize

__all__ = ["WordCount", "analyze", "count_words"]


@dataclass(frozen=True, slots=True)
class WordCount:
    """Word and character statistics for a text.

    ``total_words`` is the sum of known Khmer words, unknown Khmer word
    groups, Latin words, and number tokens (ASCII or Khmer digits).
    ``characters`` counts characters of the NFC-normalized text.
    """

    total_words: int
    khmer_words: int
    unknown_khmer_words: int
    latin_words: int
    numbers: int
    clusters: int
    khmer_characters: int
    characters: int


def analyze(text: str, lexicon: Lexicon | None = None) -> WordCount:
    """Compute word and character statistics for *text*."""
    normalized = unicodedata.normalize("NFC", text)
    tokens = tokenize(normalized, lexicon)

    khmer_words = 0
    unknown = 0
    latin = 0
    numbers = 0
    clusters = 0
    for token in tokens:
        if token.type is TokenType.KHMER_WORD:
            khmer_words += 1
            clusters += len(segment_clusters(token.text))
        elif token.type is TokenType.KHMER_UNKNOWN:
            unknown += 1
            clusters += len(segment_clusters(token.text))
        elif token.type is TokenType.LATIN:
            latin += 1
        elif token.type in (TokenType.NUMBER, TokenType.KHMER_DIGIT):
            numbers += 1
            if token.type is TokenType.KHMER_DIGIT:
                clusters += len(token.text)

    return WordCount(
        total_words=khmer_words + unknown + latin + numbers,
        khmer_words=khmer_words,
        unknown_khmer_words=unknown,
        latin_words=latin,
        numbers=numbers,
        clusters=clusters,
        khmer_characters=sum(1 for ch in normalized if is_khmer(ch)),
        characters=len(normalized),
    )


def count_words(text: str, lexicon: Lexicon | None = None) -> int:
    """Count words in *text* (Khmer words, Latin words, and numbers)."""
    return analyze(text, lexicon).total_words
