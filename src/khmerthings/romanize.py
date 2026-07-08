"""Phonetic romanization of Khmer text (UNGEGN-style).

Turns Khmer script into a readable Latin approximation of how it sounds —
e.g. ``ភ្នំពេញ`` → ``phnom penh`` — using the two-register system that
governs Khmer vowel pronunciation. This is a deterministic rule engine, not
a probabilistic transliterator, backed by a curated whole-word **exception
lexicon** (``data/romanize.txt``) that overrides the rules for irregular
words and established place-name spellings.

It is **phonetic, not reversible**: two different spellings can romanize the
same way, and the Latin output cannot be mapped back to a unique Khmer
spelling. For a lossless round-trip you would need a transliteration scheme,
which this is not.

## How it works

Text is tokenized (:func:`khmerthings.tokenizer.tokenize`) against the
caller's lexicon unioned with the exception-lexicon keys, so an exception
entry always surfaces as a single word. For each Khmer word:

1. If the whole word is in the exception lexicon, its curated spelling wins.
2. Otherwise the word is romanized cluster by cluster. Each cluster resolves
   a consonant series (1st/2nd register), an onset (base consonant plus any
   subscript consonants), and a vowel — dependent vowels read differently per
   register; a bare consonant with no vowel takes the register's inherent
   vowel unless it closes a syllable, where it reads as a final consonant.

Register shifters muusikatoan (``៉``) and triisap (``៊``) flip the register;
Khmer digits are rendered as Arabic numerals; non-Khmer runs pass through
unchanged. The rule engine is a practical approximation of UNGEGN 1972 order,
not a full phonological model — see the exception lexicon for correctness on
words the rules get wrong.
"""

from __future__ import annotations

import unicodedata

from khmerthings.chars import (
    COENG,
    is_consonant,
    is_dependent_vowel,
    is_independent_vowel,
)
from khmerthings.clusters import segment_clusters
from khmerthings.lexicon import Lexicon, default_lexicon, load_romanizations
from khmerthings.numerals import khmer_to_arabic
from khmerthings.tokenizer import TokenType, tokenize

__all__ = ["romanize"]

# --- Consonant tables -------------------------------------------------------
# Series: False = 1st register (a-series), True = 2nd register (o-series).
_SECOND_SERIES = frozenset("គឃងជឈញឌឍនទធពភមយរលវ")

# Initial (syllable-onset) romanization.
_INITIAL = {
    "ក": "k", "ខ": "kh", "គ": "k", "ឃ": "kh", "ង": "ng",
    "ច": "ch", "ឆ": "chh", "ជ": "ch", "ឈ": "chh", "ញ": "nh",
    "ដ": "d", "ឋ": "th", "ឌ": "d", "ឍ": "th", "ណ": "n",
    "ត": "t", "ថ": "th", "ទ": "t", "ធ": "th", "ន": "n",
    "ប": "b", "ផ": "ph", "ព": "p", "ភ": "ph", "ម": "m",
    "យ": "y", "រ": "r", "ល": "l", "វ": "v",
    "ស": "s", "ហ": "h", "ឡ": "l", "អ": "",
}  # fmt: skip

# Final (syllable-coda) romanization.
_FINAL = {
    "ក": "k", "ខ": "k", "គ": "k", "ឃ": "k", "ង": "ng",
    "ច": "ch", "ឆ": "ch", "ជ": "ch", "ឈ": "ch", "ញ": "nh",
    "ដ": "t", "ឋ": "t", "ឌ": "t", "ឍ": "t", "ណ": "n",
    "ត": "t", "ថ": "t", "ទ": "t", "ធ": "t", "ន": "n",
    "ប": "p", "ផ": "p", "ព": "p", "ភ": "p", "ម": "m",
    "យ": "y", "រ": "r", "ល": "l", "វ": "v",
    "ស": "s", "ហ": "h", "ឡ": "l", "អ": "",
}  # fmt: skip

# --- Vowel tables -----------------------------------------------------------
# Dependent vowels, keyed by character; value is (1st-series, 2nd-series).
_VOWELS = {
    "ា": ("a", "ea"),
    "ិ": ("e", "i"),
    "ី": ("ei", "i"),
    "ឹ": ("oe", "oe"),
    "ឺ": ("oe", "oe"),
    "ុ": ("o", "u"),
    "ូ": ("ou", "u"),
    "ួ": ("uo", "uo"),
    "ើ": ("aeu", "eu"),
    "ឿ": ("oea", "oea"),
    "ៀ": ("ie", "ie"),
    "េ": ("e", "e"),
    "ែ": ("ae", "ae"),
    "ៃ": ("ai", "ey"),
    "ោ": ("ao", "ao"),
    "ៅ": ("au", "au"),
}
# Inherent vowel (a consonant with no dependent vowel), per series.
_INHERENT = ("a", "o")

# Independent vowels carry their own vowel and take no consonant onset.
_INDEPENDENT = {
    "ឥ": "e", "ឦ": "ei", "ឧ": "o", "ឩ": "u", "ឪ": "ov",
    "ឫ": "rue", "ឬ": "rue", "ឭ": "lue", "ឮ": "lue",
    "ឯ": "ae", "ឰ": "ai", "ឱ": "ao", "ឲ": "ao", "ឳ": "au",
    "ឣ": "a", "ឤ": "a",
}  # fmt: skip

# --- Signs ------------------------------------------------------------------
_NIKAHIT = "ំ"  # U+17C6, nasal coda -> "m"
_REAHMUK = "ះ"  # U+17C7, final "h"
_MUUSIKATOAN = "៉"  # U+17C9, force 1st series
_TRIISAP = "៊"  # U+17CA, force 2nd series
# Signs that leave no romanized trace (length marks, silencers, historical).
_SILENT_SIGNS = frozenset("ៈ់៌៍៎៏័៑")


def _split_cluster(cluster: str) -> tuple[str, list[str], str, set[str]]:
    """Return (base, subscript-consonants, dependent-vowel, signs) of a cluster."""
    base = cluster[0]
    subs: list[str] = []
    vowel = ""
    signs: set[str] = set()
    i = 1
    while i < len(cluster):
        ch = cluster[i]
        if ch == COENG and i + 1 < len(cluster):
            subs.append(cluster[i + 1])
            i += 2
        elif is_dependent_vowel(ch):
            vowel = ch  # a cluster carries at most one dependent vowel
            i += 1
        else:
            signs.add(ch)
            i += 1
    return base, subs, vowel, signs


def _romanize_word(word: str) -> str:
    """Romanize a single Khmer word by rule (no exception-lexicon lookup)."""
    out: list[str] = []
    had_vowel = False  # did the current syllable already get its vowel nucleus?
    for cluster in segment_clusters(word):
        base = cluster[0]

        if is_independent_vowel(base):
            out.append(_INDEPENDENT.get(base, ""))
            had_vowel = True
            continue
        if not is_consonant(base):
            out.append(khmer_to_arabic(cluster))  # digits; else passthrough
            continue

        _, subs, vowel, signs = _split_cluster(cluster)
        onset_consonants = [base, *subs]

        # Register: last onset consonant governs the vowel, then shifters.
        series = 1 if onset_consonants[-1] in _SECOND_SERIES else 0
        if _MUUSIKATOAN in signs:
            series = 0
        elif _TRIISAP in signs:
            series = 1

        has_nucleus = bool(vowel) or _NIKAHIT in signs or _REAHMUK in signs
        is_final = not has_nucleus and had_vowel

        if is_final:
            out.append("".join(_FINAL.get(c, "") for c in onset_consonants))
            had_vowel = False
        else:
            out.append("".join(_INITIAL.get(c, "") for c in onset_consonants))
            if vowel:
                out.append(_VOWELS[vowel][series])
            else:
                out.append(_INHERENT[series])
            had_vowel = True

        if _NIKAHIT in signs:
            out.append("m")
        if _REAHMUK in signs:
            out.append("h")
        # _MUUSIKATOAN / _TRIISAP already consumed as register shifters;
        # _SILENT_SIGNS contribute nothing.

    return "".join(out)


def _exception_lexicon(lexicon: Lexicon) -> Lexicon:
    """*lexicon* plus the exception-lexicon keys, so exceptions tokenize whole."""
    return Lexicon(set(lexicon) | set(load_romanizations()))


def romanize(text: str, lexicon: Lexicon | None = None) -> str:
    """Return a phonetic Latin romanization of *text* (UNGEGN-style).

    Khmer words are looked up in the exception lexicon first and otherwise
    romanized by rule; Khmer digits become Arabic numerals; non-Khmer text
    passes through unchanged. Tokenization uses *lexicon* (default: the core
    ``"words"`` source) unioned with the exception-lexicon keys.

    Phonetic and not reversible — see the module docstring.

    >>> romanize("ភ្នំពេញ")
    'phnom penh'
    """
    if lexicon is None:
        lexicon = default_lexicon()
    text = unicodedata.normalize("NFC", text)
    exceptions = load_romanizations()
    tokens = tokenize(text, _exception_lexicon(lexicon))

    out: list[str] = []
    prev_was_word = False
    for token in tokens:
        is_word = token.type in (TokenType.KHMER_WORD, TokenType.KHMER_UNKNOWN)
        if is_word:
            # Khmer runs no spaces between words; separate romanized words so
            # the output reads as words rather than one run-on string.
            if prev_was_word:
                out.append(" ")
            out.append(exceptions.get(token.text) or _romanize_word(token.text))
        elif token.type is TokenType.KHMER_DIGIT:
            out.append(khmer_to_arabic(token.text))
        else:
            out.append(token.text)
        prev_was_word = is_word
    return "".join(out)
