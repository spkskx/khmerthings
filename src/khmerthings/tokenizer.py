"""Deterministic tokenization of mixed Khmer/Latin text.

Pipeline: NFC-normalize, split into script runs, then segment Khmer runs
into words by greedy longest-match against a lexicon over character
clusters. Clusters that match no lexicon word are grouped into single
``KHMER_UNKNOWN`` tokens rather than dropped, so tokenization is lossless:
concatenating all token texts reproduces the normalized input.

The zero-width space (U+200B) is treated as whitespace — real-world Khmer
text uses it as an explicit word delimiter.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum

from khmerthings.chars import (
    ZERO_WIDTH_SPACE,
    is_khmer_digit,
    is_khmer_letter_or_mark,
    is_khmer_punctuation,
)
from khmerthings.clusters import segment_clusters
from khmerthings.lexicon import Lexicon, default_lexicon

__all__ = ["Token", "TokenType", "tokenize"]


class TokenType(Enum):
    KHMER_WORD = "khmer_word"  # matched a lexicon word
    KHMER_UNKNOWN = "khmer_unknown"  # contiguous unmatched Khmer clusters
    LATIN = "latin"  # run of non-Khmer letters
    NUMBER = "number"  # run of ASCII digits
    KHMER_DIGIT = "khmer_digit"  # run of Khmer digits ០..៩
    PUNCT = "punct"  # punctuation (Khmer or otherwise)
    SPACE = "space"  # whitespace, including ZWSP
    OTHER = "other"  # anything else (symbols, emoji, ...)


@dataclass(frozen=True, slots=True)
class Token:
    """A tokenized span. Offsets index into the NFC-normalized input."""

    text: str
    type: TokenType
    start: int
    end: int


def _char_type(ch: str) -> TokenType:
    if ch.isspace() or ch == ZERO_WIDTH_SPACE:
        return TokenType.SPACE
    if is_khmer_digit(ch):
        return TokenType.KHMER_DIGIT
    if is_khmer_letter_or_mark(ch):
        # Khmer letters get word-segmented later; marker type for the run.
        return TokenType.KHMER_WORD
    if ch.isalpha():
        return TokenType.LATIN
    if ch.isascii() and ch.isdigit():
        return TokenType.NUMBER
    if is_khmer_punctuation(ch) or unicodedata.category(ch).startswith("P"):
        return TokenType.PUNCT
    return TokenType.OTHER


def _segment_khmer_run(run: str, offset: int, lexicon: Lexicon) -> list[Token]:
    clusters = segment_clusters(run)
    tokens: list[Token] = []
    pos = offset  # character offset of clusters[i]
    i = 0
    unknown_start: int | None = None
    unknown_pos = pos

    def flush_unknown(end_index: int, end_pos: int) -> None:
        nonlocal unknown_start
        if unknown_start is not None:
            text = "".join(clusters[unknown_start:end_index])
            tokens.append(Token(text, TokenType.KHMER_UNKNOWN, unknown_pos, end_pos))
            unknown_start = None

    while i < len(clusters):
        matched = lexicon.longest_match(clusters, i)
        if matched:
            flush_unknown(i, pos)
            text = "".join(clusters[i : i + matched])
            tokens.append(Token(text, TokenType.KHMER_WORD, pos, pos + len(text)))
            pos += len(text)
            i += matched
        else:
            if unknown_start is None:
                unknown_start = i
                unknown_pos = pos
            pos += len(clusters[i])
            i += 1
    flush_unknown(len(clusters), pos)
    return tokens


def tokenize(text: str, lexicon: Lexicon | None = None) -> list[Token]:
    """Tokenize *text* into typed spans.

    Lossless over the NFC-normalized input: the concatenation of all token
    texts equals ``unicodedata.normalize("NFC", text)``.
    """
    if lexicon is None:
        lexicon = default_lexicon()
    text = unicodedata.normalize("NFC", text)
    tokens: list[Token] = []
    i = 0
    n = len(text)
    while i < n:
        run_type = _char_type(text[i])
        j = i + 1
        while j < n and _char_type(text[j]) == run_type:
            j += 1
        run = text[i:j]
        if run_type is TokenType.KHMER_WORD:
            tokens.extend(_segment_khmer_run(run, i, lexicon))
        else:
            tokens.append(Token(run, run_type, i, j))
        i = j
    return tokens
