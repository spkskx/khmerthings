"""Khmer word breaking (word segmentation).

Khmer script writes no spaces between words, so splitting text into words
requires a dictionary. This module exposes the segmentation engine behind
:mod:`khmerthings.tokenizer` as a first-class tool:

- :func:`break_words` returns the words of a text as a list.
- :func:`mark_boundaries` returns the text unchanged except that a separator
  (zero-width space by default) is inserted at Khmer word boundaries — the
  form line-breaking engines and downstream text tools expect.
"""

from __future__ import annotations

from khmerthings.lexicon import Lexicon
from khmerthings.tokenizer import TokenType, tokenize

__all__ = ["break_words", "mark_boundaries"]

_WORD_TYPES = frozenset(
    {
        TokenType.KHMER_WORD,
        TokenType.KHMER_UNKNOWN,
        TokenType.LATIN,
        TokenType.NUMBER,
        TokenType.KHMER_DIGIT,
    }
)
_KHMER_WORD_TYPES = frozenset({TokenType.KHMER_WORD, TokenType.KHMER_UNKNOWN})


def break_words(text: str, lexicon: Lexicon | None = None) -> list[str]:
    """Split *text* into words, in order of appearance.

    Returns Khmer words (dictionary matches and unknown spans), Latin words,
    and numbers; whitespace and punctuation are excluded. The result length
    always equals :func:`khmerthings.counter.count_words` for the same text.
    """
    return [t.text for t in tokenize(text, lexicon) if t.type in _WORD_TYPES]


def mark_boundaries(text: str, separator: str = "​", lexicon: Lexicon | None = None) -> str:
    """Insert *separator* at Khmer word boundaries, leaving all else intact.

    A boundary is the position between two adjacent Khmer word tokens (known
    or unknown) with no character between them. Existing whitespace and
    punctuation are preserved as-is, so removing every *separator* from the
    result reproduces the NFC-normalized input (provided the separator does
    not itself occur in the input).
    """
    parts: list[str] = []
    previous_was_khmer_word = False
    for token in tokenize(text, lexicon):
        is_khmer_word = token.type in _KHMER_WORD_TYPES
        if previous_was_khmer_word and is_khmer_word:
            parts.append(separator)
        parts.append(token.text)
        previous_was_khmer_word = is_khmer_word
    return "".join(parts)
