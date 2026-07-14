"""Deterministic validation of Khmer orthographic structure.

Validation is conservative: it reports definite encoding-structure errors and
never rewrites text. Offsets refer to the NFC-normalized input.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum

from khmerthings.chars import (
    is_coeng,
    is_consonant,
    is_dependent_vowel,
    is_independent_vowel,
    is_inherent_vowel,
    is_sign,
)

__all__ = ["OrthographyIssue", "OrthographyIssueCode", "validate_orthography"]

_REGISTER_SHIFTERS = frozenset("៉៊")


class OrthographyIssueCode(Enum):
    """Stable machine-readable orthography issue codes."""

    ORPHAN_COENG = "orphan_coeng"
    INVALID_COENG_FOLLOWER = "invalid_coeng_follower"
    ORPHAN_MARK = "orphan_mark"
    REPEATED_DEPENDENT_VOWEL = "repeated_dependent_vowel"
    REPEATED_REGISTER_SHIFTER = "repeated_register_shifter"
    INVALID_MARK_ORDER = "invalid_mark_order"


@dataclass(frozen=True)
class OrthographyIssue:
    """One definite structural issue in NFC-normalized Khmer text."""

    text: str
    start: int
    end: int
    code: OrthographyIssueCode


def validate_orthography(text: str) -> tuple[OrthographyIssue, ...]:
    """Return definite Khmer encoding-structure issues in *text*.

    Non-Khmer text is ignored. This conservative validator checks orphaned
    marks/coeng, coeng followers, duplicate vowels/register shifters, and the
    order register-shifter → dependent-vowel → other signs.
    """
    text = unicodedata.normalize("NFC", text)
    issues: list[OrthographyIssue] = []
    active = False
    vowel_seen = False
    shifter_seen = False
    trailing_sign_seen = False
    i = 0

    while i < len(text):
        ch = text[i]
        if is_consonant(ch) or is_independent_vowel(ch):
            active = True
            vowel_seen = shifter_seen = trailing_sign_seen = False
        elif is_coeng(ch):
            if not active or i + 1 == len(text):
                issues.append(OrthographyIssue(ch, i, i + 1, OrthographyIssueCode.ORPHAN_COENG))
                active = False
            elif not is_consonant(text[i + 1]):
                end = i + 2
                issues.append(
                    OrthographyIssue(
                        text[i:end], i, end, OrthographyIssueCode.INVALID_COENG_FOLLOWER
                    )
                )
                active = False
                i += 1
        elif is_dependent_vowel(ch) or is_inherent_vowel(ch):
            if not active:
                issues.append(OrthographyIssue(ch, i, i + 1, OrthographyIssueCode.ORPHAN_MARK))
            elif vowel_seen:
                issues.append(
                    OrthographyIssue(ch, i, i + 1, OrthographyIssueCode.REPEATED_DEPENDENT_VOWEL)
                )
            elif trailing_sign_seen:
                issues.append(
                    OrthographyIssue(ch, i, i + 1, OrthographyIssueCode.INVALID_MARK_ORDER)
                )
            vowel_seen = True
        elif is_sign(ch):
            if not active:
                issues.append(OrthographyIssue(ch, i, i + 1, OrthographyIssueCode.ORPHAN_MARK))
            elif ch in _REGISTER_SHIFTERS:
                if shifter_seen:
                    issues.append(
                        OrthographyIssue(
                            ch, i, i + 1, OrthographyIssueCode.REPEATED_REGISTER_SHIFTER
                        )
                    )
                elif vowel_seen or trailing_sign_seen:
                    issues.append(
                        OrthographyIssue(ch, i, i + 1, OrthographyIssueCode.INVALID_MARK_ORDER)
                    )
                shifter_seen = True
            else:
                trailing_sign_seen = True
        else:
            active = False
        i += 1

    return tuple(sorted(issues, key=lambda issue: (issue.start, issue.end, issue.code.value)))
