"""Khmer spell checking and spell fixing.

Detection is purely dictionary-driven, so both tools improve automatically
as the lexicon data files grow:

- A Khmer span is an issue either because it is a *known misspelling* from
  the variants map (``VARIANT``, with its canonical spelling as the single
  suggestion) or because it matches no lexicon word at all (``UNKNOWN``,
  with suggestions ranked by cluster edit distance, pronunciation, NiDA
  keyboard proximity, then Khmer dictionary order).
- :func:`check_variants` reports only ``VARIANT`` issues (cheap dictionary
  lookup); :func:`check_unknown` reports only ``UNKNOWN`` issues (the
  expensive edit-distance search, for suggestions); :func:`check_spelling`
  merges both, sorted by position. None of them modify text.
- :func:`fix_spelling` rewrites only known misspellings to their canonical
  spelling and copies everything else verbatim. Unknown words are never
  auto-fixed — a word missing from the lexicon is not proof it is wrong.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from functools import cache

from khmerthings.clusters import segment_clusters
from khmerthings.lexicon import Lexicon, _checking_lexicon, default_lexicon, load_variants
from khmerthings.romanize import _romanize_word
from khmerthings.sorting import SortKey, khmer_sort_key
from khmerthings.tokenizer import TokenType, tokenize

__all__ = [
    "IssueKind",
    "SpellIssue",
    "check_spelling",
    "check_unknown",
    "check_variants",
    "fix_spelling",
]

#: Unknown spans longer than this (in clusters) get no suggestions: greedy
#: segmentation lumps adjacent unknown words into one span, and edit-distance
#: suggestions against single lexicon words would be meaningless for it.
_MAX_SUGGEST_CLUSTERS = 8

# Physical positions on the standard NiDA desktop layout. Shifted and
# unshifted Khmer characters share a key; only letters and marks matter here.
_NIDA_ROWS = (
    ("ឆឹេរតយុិោផៀឪ", "ឈឺែឬទួូីៅភឿឧ"),
    ("ាសដថងហ្កលើ់", "ាំៃឌធអះញគឡោះ"),
    ("ឋខចវបនមុំ។៊", "ឍឃជេះពណំុះ៕?"),
)
_NIDA_POSITION = {
    char: (row, column)
    for row, states in enumerate(_NIDA_ROWS)
    for state in states
    for column, char in enumerate(state)
}


class IssueKind(Enum):
    VARIANT = "variant"  # known misspelling from the variants map
    UNKNOWN = "unknown"  # Khmer span matching no lexicon word


@dataclass(frozen=True, slots=True)
class SpellIssue:
    """A spelling issue found in a text. Offsets index the NFC input."""

    text: str
    kind: IssueKind
    start: int
    end: int
    suggestions: tuple[str, ...]


@cache
def _clusterized(lexicon: Lexicon) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Each lexicon word with its cluster sequence, in sorted word order."""
    return tuple((word, tuple(segment_clusters(word))) for word in lexicon)


def _edit_distance_within(a: Sequence[str], b: Sequence[str], bound: int) -> int | None:
    """Levenshtein distance between cluster sequences, or None if > *bound*."""
    if abs(len(a) - len(b)) > bound:
        return None
    previous = list(range(len(b) + 1))
    for i, cluster_a in enumerate(a, 1):
        current = [i]
        for j, cluster_b in enumerate(b, 1):
            cost = 0 if cluster_a == cluster_b else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))
        if min(current) > bound:
            return None
        previous = current
    return previous[-1] if previous[-1] <= bound else None


def _keyboard_distance(a: Sequence[str], b: Sequence[str]) -> int:
    """NiDA physical-key distance for substitutions at aligned cluster positions."""
    score = 0
    for cluster_a, cluster_b in zip(a, b, strict=False):
        if cluster_a == cluster_b:
            continue
        position_a = _NIDA_POSITION.get(cluster_a[0])
        position_b = _NIDA_POSITION.get(cluster_b[0])
        if position_a is not None and position_b is not None:
            score += abs(position_a[0] - position_b[0]) + abs(position_a[1] - position_b[1])
        else:
            score += 99
    return score


def _suggest(span: str, lexicon: Lexicon, max_suggestions: int) -> tuple[str, ...]:
    """Lexicon words nearest by spelling, sound, keyboard, then Khmer order."""
    if max_suggestions <= 0:
        return ()
    clusters = segment_clusters(span)
    if len(clusters) > _MAX_SUGGEST_CLUSTERS:
        return ()
    bound = 1 if len(clusters) <= 3 else 2
    pronunciation = tuple(_romanize_word(span))
    ranked: list[tuple[int, int, int, SortKey, str]] = []
    for word, word_clusters in _clusterized(lexicon):
        distance = _edit_distance_within(clusters, word_clusters, bound)
        if distance is not None:
            word_pronunciation = tuple(_romanize_word(word))
            phonetic = _edit_distance_within(
                pronunciation,
                word_pronunciation,
                max(len(pronunciation), len(word_pronunciation)),
            )
            assert phonetic is not None
            ranked.append(
                (
                    distance,
                    phonetic,
                    _keyboard_distance(clusters, word_clusters),
                    khmer_sort_key(word),
                    word,
                )
            )
    ranked.sort()
    return tuple(word for _, _, _, _, word in ranked[:max_suggestions])


def check_variants(text: str, lexicon: Lexicon | None = None) -> list[SpellIssue]:
    """Report known-misspelling (``VARIANT``) issues in *text*, in order of appearance.

    Fast: pure dictionary lookup, no edit-distance search. Tokenizes with
    *lexicon* (default: the core ``"words"`` source) extended by the variant
    misspellings; a token that is a variant misspelling — and not itself a
    word of *lexicon* — becomes a ``VARIANT`` issue whose only suggestion is
    the canonical spelling. Never reports ``UNKNOWN`` issues; see
    :func:`check_unknown` for those.
    """
    if lexicon is None:
        lexicon = default_lexicon()
    variants = load_variants()
    issues: list[SpellIssue] = []
    for token in tokenize(text, _checking_lexicon(lexicon)):
        if (
            token.type is TokenType.KHMER_WORD
            and token.text in variants
            and token.text not in lexicon
        ):
            canonical = variants[token.text]
            issues.append(
                SpellIssue(token.text, IssueKind.VARIANT, token.start, token.end, (canonical,))
            )
    return issues


def check_unknown(
    text: str, lexicon: Lexicon | None = None, *, max_suggestions: int = 3
) -> list[SpellIssue]:
    """Report unmatched-Khmer-span (``UNKNOWN``) issues in *text*, in order of appearance.

    The expensive path: every unmatched Khmer span is edit-distance-searched
    against the whole lexicon for suggestions. Tokenizes with *lexicon*
    (default: the core ``"words"`` source) extended by the variant
    misspellings, so known misspellings are excluded here (they surface as
    single ``KHMER_WORD`` tokens, not ``KHMER_UNKNOWN``); see
    :func:`check_variants` for those. Never reports ``VARIANT`` issues.
    """
    if lexicon is None:
        lexicon = default_lexicon()
    issues: list[SpellIssue] = []
    for token in tokenize(text, _checking_lexicon(lexicon)):
        if token.type is TokenType.KHMER_UNKNOWN:
            suggestions = _suggest(token.text, lexicon, max_suggestions)
            issues.append(
                SpellIssue(token.text, IssueKind.UNKNOWN, token.start, token.end, suggestions)
            )
    return issues


def check_spelling(
    text: str, lexicon: Lexicon | None = None, *, max_suggestions: int = 3
) -> list[SpellIssue]:
    """Report spelling issues in *text*, in order of appearance.

    A thin wrapper merging :func:`check_variants` and :func:`check_unknown`,
    sorted by position. A token that is a variant misspelling — and not
    itself a word of *lexicon* — becomes a ``VARIANT`` issue whose only
    suggestion is the canonical spelling. An unmatched Khmer span becomes an
    ``UNKNOWN`` issue with up to *max_suggestions* nearby lexicon words as
    suggestions (never variant misspellings). Non-Khmer text is ignored.
    """
    if lexicon is None:
        lexicon = default_lexicon()
    issues = check_variants(text, lexicon) + check_unknown(
        text, lexicon, max_suggestions=max_suggestions
    )
    issues.sort(key=lambda issue: issue.start)
    return issues


def fix_spelling(text: str, lexicon: Lexicon | None = None) -> str:
    """Rewrite known misspellings in *text* to their canonical spelling.

    Only variant misspellings (that are not words of *lexicon* themselves)
    are replaced; unknown words, known words, and non-Khmer text are copied
    verbatim, so on text without variant misspellings this returns the
    NFC-normalized input unchanged. Idempotent.
    """
    if lexicon is None:
        lexicon = default_lexicon()
    variants = load_variants()
    parts: list[str] = []
    for token in tokenize(text, _checking_lexicon(lexicon)):
        if (
            token.type is TokenType.KHMER_WORD
            and token.text in variants
            and token.text not in lexicon
        ):
            parts.append(variants[token.text])
        else:
            parts.append(token.text)
    return "".join(parts)
