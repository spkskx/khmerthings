"""Text normalization: spellfix plus segmentation-aware spacing.

Combines the spellfixer's variant corrections with word-boundary spacing
(inserting the zero-width word delimiter where nothing currently separates
two Khmer words, the same rule :func:`khmerthings.segmenter.mark_boundaries`
uses) and Khmer sentence-stop spacing (no space before ។/៕, exactly one
space after), turning loosely-typed raw Khmer text into clean, ready-to-use
text in one pass.
"""

from __future__ import annotations

from khmerthings.chars import ZERO_WIDTH_SPACE, is_khmer_sentence_stop
from khmerthings.lexicon import Lexicon, _checking_lexicon, default_lexicon, load_variants
from khmerthings.tokenizer import Token, TokenType, tokenize

__all__ = ["normalize_text"]

_WORD_TYPES = frozenset(
    {
        TokenType.KHMER_WORD,
        TokenType.KHMER_UNKNOWN,
        TokenType.LATIN,
        TokenType.NUMBER,
        TokenType.KHMER_DIGIT,
    }
)


def _is_stop(token: Token) -> bool:
    return (
        token.type is TokenType.PUNCT
        and len(token.text) == 1
        and is_khmer_sentence_stop(token.text)
    )


def _separator(prev: Token, current: Token, pending_space: str | None) -> str:
    if _is_stop(current):
        return ""
    if _is_stop(prev):
        return " "
    prev_is_word = prev.type in _WORD_TYPES
    curr_is_word = current.type in _WORD_TYPES
    if prev_is_word and curr_is_word:
        if pending_space and set(pending_space) != {ZERO_WIDTH_SPACE}:
            return " "
        return ZERO_WIDTH_SPACE
    return " " if pending_space else ""


def normalize_text(text: str, lexicon: Lexicon | None = None) -> str:
    """Return *text* spellfixed, re-spaced, and sentence-stop-tidied.

    Tokenizes *text* (NFC-normalized) against *lexicon* (default: the core
    ``"words"`` source) plus the variant misspellings, then rebuilds it:

    - Known misspellings are rewritten to their canonical spelling (same
      rule as :func:`khmerthings.spellcheck.fix_spelling`).
    - A zero-width space is inserted between adjacent Khmer/Latin/number
      word tokens that have no separator at all; an existing visible space
      between such tokens is collapsed to a single ``" "`` rather than
      downgraded to invisible. Runs of whitespace elsewhere collapse to a
      single ``" "``; leading and trailing whitespace is dropped.
    - Whitespace immediately before a Khmer sentence stop (។, ៕) is
      dropped, and exactly one space is ensured immediately after it.

    Idempotent: normalizing already-normalized text returns it unchanged.
    """
    if lexicon is None:
        lexicon = default_lexicon()
    variants = load_variants()
    tokens = tokenize(text, _checking_lexicon(lexicon))

    parts: list[str] = []
    prev: Token | None = None
    pending_space: str | None = None

    for token in tokens:
        if token.type is TokenType.SPACE:
            pending_space = (pending_space or "") + token.text
            continue

        token_text = token.text
        if (
            token.type is TokenType.KHMER_WORD
            and token_text in variants
            and token_text not in lexicon
        ):
            token_text = variants[token_text]

        if prev is not None:
            parts.append(_separator(prev, token, pending_space))
        parts.append(token_text)

        prev = token
        pending_space = None

    return "".join(parts)
