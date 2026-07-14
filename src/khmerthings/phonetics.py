"""Private phonetic approximation used to rank spelling suggestions."""

from __future__ import annotations

from khmerthings.chars import (
    COENG,
    is_consonant,
    is_dependent_vowel,
    is_independent_vowel,
)
from khmerthings.clusters import segment_clusters

__all__: list[str] = []

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
            out.append(cluster)
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
