"""Khmer numeral conversion: digits and spelled-out numbers.

Three deterministic, rule-based operations:

- :func:`arabic_to_khmer` / :func:`khmer_to_arabic` transliterate the ten
  digit characters between Arabic (``0``-``9``) and Khmer (``០``-``៩``,
  U+17E0-U+17E9). Only digit characters are touched; everything else passes
  through unchanged, so the two functions round-trip on the digit subset.
- :func:`number_to_words` spells a non-negative-or-negative integer in Khmer
  using the traditional decimal-unit system (ដប់, រយ, ពាន់, ម៉ឺន, សែន, លាន,
  …). The unit words are fixed grammar, not curated vocabulary, so they live
  in-module rather than in a data file.
"""

from __future__ import annotations

__all__ = ["arabic_to_khmer", "khmer_to_arabic", "number_to_words"]

_KHMER_ZERO = 0x17E0  # ០

# Digit-only translation tables (str.translate maps codepoint -> codepoint).
_TO_KHMER = {ord("0") + i: _KHMER_ZERO + i for i in range(10)}
_TO_ARABIC = {_KHMER_ZERO + i: ord("0") + i for i in range(10)}

# Spelled-out number pieces.
_ONES = ("", "មួយ", "ពីរ", "បី", "បួន", "ប្រាំ", "ប្រាំមួយ", "ប្រាំពីរ", "ប្រាំបី", "ប្រាំបួន")
_TENS = {
    2: "ម្ភៃ",
    3: "សាមសិប",
    4: "សែសិប",
    5: "ហាសិប",
    6: "ហុកសិប",
    7: "ចិតសិប",
    8: "ប៉ែតសិប",
    9: "កៅសិប",
}
# Decimal-unit words, largest first. Numbers at or above one million recurse
# through "លាន": e.g. 10^7 -> ដប់លាន, 10^9 -> ពាន់លាន.
_UNITS = ((1_000_000, "លាន"), (100_000, "សែន"), (10_000, "ម៉ឺន"), (1_000, "ពាន់"), (100, "រយ"))

_ZERO_WORD = "សូន្យ"
_MINUS_WORD = "ដក"  # negative-sign word, e.g. -5 -> ដកប្រាំ


def arabic_to_khmer(text: str) -> str:
    """Return *text* with Arabic digits ``0``-``9`` replaced by Khmer ``០``-``៩``.

    Only digit characters change; all other characters (including Khmer
    digits already present) are left untouched.

    >>> arabic_to_khmer("A320")
    'A៣២០'
    """
    return text.translate(_TO_KHMER)


def khmer_to_arabic(text: str) -> str:
    """Return *text* with Khmer digits ``០``-``៩`` replaced by Arabic ``0``-``9``.

    The inverse of :func:`arabic_to_khmer` on the digit subset.

    >>> khmer_to_arabic("A៣២០")
    'A320'
    """
    return text.translate(_TO_ARABIC)


def _spell(n: int) -> str:
    """Spell a strictly positive integer (no sign, no zero handling)."""
    if n < 10:
        return _ONES[n]
    if n < 20:
        return "ដប់" + _ONES[n - 10]
    if n < 100:
        return _TENS[n // 10] + _ONES[n % 10]
    for value, word in _UNITS:
        if n >= value:
            return _spell(n // value) + word + (_spell(n % value) if n % value else "")
    raise AssertionError("unreachable")  # pragma: no cover


def number_to_words(n: int) -> str:
    """Spell the integer *n* in Khmer words.

    Zero is ``សូន្យ``; negative numbers are prefixed with ``ដក``. The decimal
    units ដប់/រយ/ពាន់/ម៉ឺន/សែន/លាន compose left to right, recursing through
    ``លាន`` above one million.

    >>> number_to_words(0)
    'សូន្យ'
    >>> number_to_words(123)
    'មួយរយម្ភៃបី'
    >>> number_to_words(-5)
    'ដកប្រាំ'
    """
    if n == 0:
        return _ZERO_WORD
    if n < 0:
        return _MINUS_WORD + _spell(-n)
    return _spell(n)
