"""Content-word extraction: drop function words, keep the meaning.

``condense`` is a *lossy* tool. It tokenizes text and removes stopwords —
function words carrying little standalone meaning (particles, politeness
markers, fillers, prepositions, conjunctions, demonstratives) — leaving the
content-bearing tokens behind. The result is a terse, "telegraphic" rendering
useful as a pre-processing stage for downstream analysis (e.g. intent
detection), which wants to reason over meaningful words only.

Each stopword is tagged with a category in ``data/stopwords.txt``. Categories
that *carry* intent — pronouns, auxiliaries/modals (ចង់/ត្រូវ/អាច …), and
question words — are **kept by default** and only removed when explicitly
requested via *remove*. The default therefore strips the low-information
categories only (:data:`DEFAULT_REMOVE`).

Unknown Khmer spans, Latin words, and numbers are always kept as content;
punctuation and whitespace are dropped.
"""

from __future__ import annotations

from functools import cache

from khmerthings.chars import ZERO_WIDTH_SPACE
from khmerthings.lexicon import (
    STOPWORD_CATEGORIES,
    Lexicon,
    default_lexicon,
    load_stopwords,
)
from khmerthings.tokenizer import Token, TokenType, tokenize

__all__ = ["DEFAULT_REMOVE", "condense_text", "content_tokens", "content_words"]

#: Stopword categories stripped by default. The intent-bearing categories
#: (``pronoun``, ``auxiliary``, ``question``) are deliberately excluded, so
#: content_words keeps them unless the caller adds them to *remove*.
DEFAULT_REMOVE: frozenset[str] = frozenset(
    {"particle", "politeness", "filler", "preposition", "conjunction", "demonstrative"}
)

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


def _resolve_remove(remove: frozenset[str] | set[str] | None) -> frozenset[str]:
    if remove is None:
        return DEFAULT_REMOVE
    unknown = set(remove) - STOPWORD_CATEGORIES
    if unknown:
        raise ValueError(
            f"unknown stopword categor{'y' if len(unknown) == 1 else 'ies'} "
            f"{', '.join(sorted(unknown))}; allowed: {', '.join(sorted(STOPWORD_CATEGORIES))}"
        )
    return frozenset(remove)


def content_tokens(
    text: str,
    lexicon: Lexicon | None = None,
    *,
    remove: frozenset[str] | set[str] | None = None,
) -> list[Token]:
    """Return the content-bearing word tokens of *text*, stopwords removed.

    Tokenizes *text* against *lexicon* (default: the core ``"words"`` source)
    unioned with every stopword, so stopwords always surface as single tokens
    regardless of the chosen lexicon. Keeps Khmer words, unknown Khmer spans,
    Latin words, and numbers; drops punctuation, whitespace, and any Khmer
    word whose stopword category is in *remove* (default:
    :data:`DEFAULT_REMOVE`).
    """
    if lexicon is None:
        lexicon = default_lexicon()
    removing = _resolve_remove(remove)
    stopwords = load_stopwords()
    tokens = tokenize(text, _content_lexicon(lexicon))
    kept: list[Token] = []
    for token in tokens:
        if token.type not in _WORD_TYPES:
            continue
        if token.type is TokenType.KHMER_WORD:
            category = stopwords.get(token.text)
            if category is not None and category in removing:
                continue
        kept.append(token)
    return kept


def content_words(
    text: str,
    lexicon: Lexicon | None = None,
    *,
    remove: frozenset[str] | set[str] | None = None,
) -> list[str]:
    """Return the meaningful words of *text*, in order, stopwords removed.

    The list form of :func:`content_tokens` — the input a downstream analyzer
    (e.g. intent detection) consumes.
    """
    return [t.text for t in content_tokens(text, lexicon, remove=remove)]


def condense_text(
    text: str,
    lexicon: Lexicon | None = None,
    *,
    remove: frozenset[str] | set[str] | None = None,
) -> str:
    """Return *text* condensed to its content words as a single string.

    Adjacent Khmer content words are joined by a zero-width space (the Khmer
    word delimiter, as :func:`khmerthings.segmenter.mark_boundaries` uses);
    a normal space separates a Khmer word from an adjacent Latin word or
    number. Lossy: function words and punctuation are gone.
    """
    parts: list[str] = []
    prev_is_khmer = False
    for i, token in enumerate(content_tokens(text, lexicon, remove=remove)):
        is_khmer = token.type in _KHMER_WORD_TYPES
        if i:
            parts.append(ZERO_WIDTH_SPACE if prev_is_khmer and is_khmer else " ")
        parts.append(token.text)
        prev_is_khmer = is_khmer
    return "".join(parts)


@cache
def _content_lexicon(lexicon: Lexicon) -> Lexicon:
    """*lexicon* plus every stopword, so stopwords tokenize as single words."""
    return Lexicon(set(lexicon) | set(load_stopwords()))
