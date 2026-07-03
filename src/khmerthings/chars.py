"""Khmer Unicode character classification.

Covers the Khmer block (U+1780-U+17FF) and Khmer Symbols block
(U+19E0-U+19FF). All functions are pure and operate on single characters;
multi-character strings raise ``ValueError`` to catch misuse early.
"""

from __future__ import annotations

from enum import Enum

COENG = "្"
ZERO_WIDTH_SPACE = "​"

# Invisible, deprecated "inherent vowel" format characters that still occur
# in real-world text; they always belong to the preceding cluster.
INHERENT_VOWELS = ("឴", "឵")

_CONSONANTS = range(0x1780, 0x17A3)  # ក..អ
_INDEPENDENT_VOWELS = range(0x17A3, 0x17B4)  # ឣ..ឳ (includes deprecated ឣឤ)
_DEPENDENT_VOWELS = range(0x17B6, 0x17C6)  # ា..ៅ
_SIGNS = frozenset(range(0x17C6, 0x17D2)) | {0x17DD}  # ំ..៑ + ៝ (not coeng)
_DIGITS = range(0x17E0, 0x17EA)  # ០..៩
_PUNCTUATION = frozenset(range(0x17D4, 0x17DB)) | {0x17DC}  # ។៕៖ៗ៘៙៚ + ៜ
_KHMER_BLOCK = range(0x1780, 0x1800)
_KHMER_SYMBOLS = range(0x19E0, 0x1A00)


class ScriptClass(Enum):
    """Coarse script classification of a single character."""

    KHMER = "khmer"
    LATIN = "latin"
    DIGIT = "digit"
    OTHER = "other"


def _codepoint(ch: str) -> int:
    if len(ch) != 1:
        raise ValueError(f"expected a single character, got {ch!r}")
    return ord(ch)


def is_khmer(ch: str) -> bool:
    """True if *ch* is in the Khmer or Khmer Symbols Unicode blocks."""
    cp = _codepoint(ch)
    return cp in _KHMER_BLOCK or cp in _KHMER_SYMBOLS


def is_consonant(ch: str) -> bool:
    """True for the 33 Khmer consonants ក (U+1780) through អ (U+17A2)."""
    return _codepoint(ch) in _CONSONANTS


def is_independent_vowel(ch: str) -> bool:
    """True for independent vowels ឣ (U+17A3) through ឳ (U+17B3)."""
    return _codepoint(ch) in _INDEPENDENT_VOWELS


def is_dependent_vowel(ch: str) -> bool:
    """True for dependent (combining) vowels ា (U+17B6) through ៅ (U+17C5)."""
    return _codepoint(ch) in _DEPENDENT_VOWELS


def is_sign(ch: str) -> bool:
    """True for combining signs/diacritics (nikahit, reahmuk, bantoc, ...)."""
    return _codepoint(ch) in _SIGNS


def is_coeng(ch: str) -> bool:
    """True for the subscript-forming sign ្ (U+17D2)."""
    return ch == COENG


def is_inherent_vowel(ch: str) -> bool:
    """True for the invisible deprecated inherent vowels U+17B4 and U+17B5."""
    return ch in INHERENT_VOWELS


def is_khmer_digit(ch: str) -> bool:
    """True for Khmer digits ០ (U+17E0) through ៩ (U+17E9)."""
    return _codepoint(ch) in _DIGITS


def is_khmer_punctuation(ch: str) -> bool:
    """True for Khmer punctuation such as ។ (khan) and ៕ (bariyoosan).

    The currency sign ៛ (U+17DB) is deliberately excluded.
    """
    return _codepoint(ch) in _PUNCTUATION


def is_khmer_letter_or_mark(ch: str) -> bool:
    """True if *ch* can be part of a Khmer word (letters and combining marks)."""
    return (
        is_consonant(ch)
        or is_independent_vowel(ch)
        or is_dependent_vowel(ch)
        or is_sign(ch)
        or is_coeng(ch)
        or is_inherent_vowel(ch)
    )


def khmer_digit_to_int(ch: str) -> int:
    """Convert a single Khmer digit to its integer value.

    Raises ``ValueError`` for anything that is not a Khmer digit.
    """
    cp = _codepoint(ch)
    if cp not in _DIGITS:
        raise ValueError(f"not a Khmer digit: {ch!r}")
    return cp - 0x17E0


def script_class(ch: str) -> ScriptClass:
    """Classify a character as KHMER, LATIN, DIGIT (ASCII), or OTHER.

    Khmer digits classify as KHMER; use :func:`is_khmer_digit` to
    distinguish them.
    """
    cp = _codepoint(ch)
    if cp in _KHMER_BLOCK or cp in _KHMER_SYMBOLS:
        return ScriptClass.KHMER
    if ch.isascii() and ch.isalpha():
        return ScriptClass.LATIN
    if ch.isascii() and ch.isdigit():
        return ScriptClass.DIGIT
    return ScriptClass.OTHER
