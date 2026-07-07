"""Text normalization: spellfix plus segmentation-aware spacing.

``normalize_text`` composes three independent passes, each also usable on
its own:

- :func:`khmerthings.spellcheck.fix_spelling` rewrites known misspellings
  to their canonical spelling.
- :func:`space_words` inserts a hidden zero-width word delimiter where
  nothing currently separates two Khmer words (the same rule
  :func:`khmerthings.segmenter.mark_boundaries` uses) and collapses/trims
  whitespace elsewhere.
- :func:`space_sentences` tidies Khmer sentence-stop spacing (no space
  before ។/៕, exactly one space after) — a pure string scan, no lexicon.

Together they turn loosely-typed raw Khmer text into clean, ready-to-use
text in one pass.
"""

from __future__ import annotations

import unicodedata

from khmerthings.chars import ZERO_WIDTH_SPACE, is_khmer_punctuation, is_khmer_sentence_stop
from khmerthings.lexicon import Lexicon, _checking_lexicon, default_lexicon
from khmerthings.spellcheck import fix_spelling
from khmerthings.tokenizer import Token, TokenType, tokenize

__all__ = ["normalize_text", "space_sentences", "space_words"]

_WORD_TYPES = frozenset(
    {
        TokenType.KHMER_WORD,
        TokenType.KHMER_UNKNOWN,
        TokenType.LATIN,
        TokenType.NUMBER,
        TokenType.KHMER_DIGIT,
    }
)


def _word_separator(prev: Token, current: Token, pending_space: str | None) -> str:
    prev_is_word = prev.type in _WORD_TYPES
    curr_is_word = current.type in _WORD_TYPES
    if prev_is_word and curr_is_word:
        if pending_space and set(pending_space) != {ZERO_WIDTH_SPACE}:
            return " "
        return ZERO_WIDTH_SPACE
    return " " if pending_space else ""


def space_words(text: str, lexicon: Lexicon | None = None) -> str:
    """Return *text* with hidden word-boundary spaces placed and whitespace collapsed.

    Tokenizes *text* (NFC-normalized) against *lexicon* (default: the core
    ``"words"`` source) plus the variant misspellings, then rebuilds it: a
    zero-width space is inserted between adjacent Khmer/Latin/number word
    tokens that have no separator at all; an existing visible space between
    such tokens is collapsed to a single ``" "`` rather than downgraded to
    invisible. Runs of whitespace elsewhere collapse to a single ``" "``;
    leading and trailing whitespace is dropped.

    Does not fix spellings — see :func:`khmerthings.spellcheck.fix_spelling`
    — and does not tidy Khmer sentence-stop spacing — see
    :func:`space_sentences`.
    """
    if lexicon is None:
        lexicon = default_lexicon()
    tokens = tokenize(text, _checking_lexicon(lexicon))

    parts: list[str] = []
    prev: Token | None = None
    pending_space: str | None = None

    for token in tokens:
        if token.type is TokenType.SPACE:
            pending_space = (pending_space or "") + token.text
            continue

        if prev is not None:
            parts.append(_word_separator(prev, token, pending_space))
        parts.append(token.text)

        prev = token
        pending_space = None

    return "".join(parts)


def _is_punct_char(ch: str) -> bool:
    return is_khmer_punctuation(ch) or unicodedata.category(ch).startswith("P")


def space_sentences(text: str) -> str:
    """Return *text* with Khmer sentence-stop (។, ៕) spacing tidied.

    A pure string scan — no tokenizer, no lexicon. A Khmer sentence stop is
    "isolated" if the character immediately before and after it (in the
    original text) is not itself punctuation, so runs of adjacent
    punctuation (e.g. ``។។``) are left untouched. For each isolated stop:
    whitespace immediately before it is dropped, and whitespace immediately
    after it collapses to exactly one space — unless only whitespace (or
    nothing) follows through the end of the text, in which case it is
    dropped like trailing whitespace rather than forced into a space.
    """
    text = unicodedata.normalize("NFC", text)
    n = len(text)
    out: list[str] = []
    i = 0
    while i < n:
        ch = text[i]
        isolated_stop = (
            is_khmer_sentence_stop(ch)
            and (i == 0 or not _is_punct_char(text[i - 1]))
            and (i == n - 1 or not _is_punct_char(text[i + 1]))
        )
        if isolated_stop:
            while out and (out[-1].isspace() or out[-1] == ZERO_WIDTH_SPACE):
                out.pop()
            out.append(ch)
            i += 1
            j = i
            while j < n and (text[j].isspace() or text[j] == ZERO_WIDTH_SPACE):
                j += 1
            if j < n:
                out.append(" ")
            i = j
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def normalize_text(text: str, lexicon: Lexicon | None = None) -> str:
    """Return *text* spellfixed, re-spaced, and sentence-stop-tidied.

    A composition of :func:`khmerthings.spellcheck.fix_spelling`,
    :func:`space_words`, and :func:`space_sentences` — see each for the
    exact rule it applies.

    Idempotent: normalizing already-normalized text returns it unchanged.
    """
    if lexicon is None:
        lexicon = default_lexicon()
    return space_sentences(space_words(fix_spelling(text, lexicon), lexicon))
