"""Khmer word lexicon with longest-match lookup.

The lexicon is a trie keyed by character clusters (not codepoints), so a
match can never end in the middle of a cluster. ``longest_match`` is the
core primitive for greedy word segmentation and, later, the word breaker.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Iterator, Sequence
from functools import cache
from importlib import resources

from khmerthings.chars import ZERO_WIDTH_SPACE, is_khmer_letter_or_mark
from khmerthings.clusters import segment_clusters

__all__ = [
    "STOPWORD_CATEGORIES",
    "WORD_SOURCES",
    "Lexicon",
    "default_lexicon",
    "load_lexicon",
    "load_stopwords",
    "load_variants",
]

#: Closed set of stopword categories used by ``stopwords.txt`` and the
#: :mod:`khmerthings.condense` content-word extractor.
STOPWORD_CATEGORIES: frozenset[str] = frozenset(
    {
        "particle",
        "politeness",
        "filler",
        "preposition",
        "conjunction",
        "demonstrative",
        "pronoun",
        "auxiliary",
        "question",
    }
)

#: Filename of the two-column stopword data file (word<TAB>category).
_STOPWORDS_FILE = "stopwords.txt"

#: Built-in wordlist sources shipped with the package. Each is an
#: independently curated, growable data file under ``khmerthings/data/``:
#: - "words": core vocabulary (the default)
#: - "names": personal names, surnames, honorific titles
#: - "modern": slang, informal register, loanwords, trending vocabulary
#: - "variants": common misspellings mapped to their canonical spelling
#:   (two-column file; as a lexicon source it contributes the misspellings,
#:   see :func:`load_variants` for the mapping itself)
WORD_SOURCES: dict[str, str] = {
    "words": "words.txt",
    "names": "names.txt",
    "modern": "modern.txt",
    "variants": "variants.txt",
}

_END = "\x00"  # trie sentinel; cannot collide with any cluster


class Lexicon:
    """An immutable set of Khmer words supporting longest-match lookup."""

    def __init__(self, words: Iterable[str]) -> None:
        self._words: set[str] = set()
        self._trie: dict[str, object] = {}
        for word in words:
            self._add(word)

    def _add(self, word: str) -> None:
        if not word:
            raise ValueError("empty word")
        if unicodedata.normalize("NFC", word) != word:
            raise ValueError(f"word is not NFC-normalized: {word!r}")
        if not all(is_khmer_letter_or_mark(ch) for ch in word):
            raise ValueError(f"word contains non-Khmer characters: {word!r}")
        if word in self._words:
            raise ValueError(f"duplicate word: {word!r}")
        self._words.add(word)
        node = self._trie
        for cluster in segment_clusters(word):
            node = node.setdefault(cluster, {})  # type: ignore[assignment]
        node[_END] = True

    @classmethod
    def from_lines(cls, lines: Iterable[str]) -> Lexicon:
        """Build a lexicon from wordlist lines.

        Blank lines and lines starting with ``#`` are ignored; other lines
        are stripped of surrounding whitespace (including ZWSP).
        """
        words = []
        for line in lines:
            word = line.strip().strip(ZERO_WIDTH_SPACE)
            if word and not word.startswith("#"):
                words.append(word)
        return cls(words)

    def __contains__(self, word: str) -> bool:
        return word in self._words

    def __len__(self) -> int:
        return len(self._words)

    def __iter__(self) -> Iterator[str]:
        return iter(sorted(self._words))

    def longest_match(self, clusters: Sequence[str], start: int = 0) -> int:
        """Length in clusters of the longest word starting at *start*.

        Returns 0 if no word in the lexicon matches there.
        """
        node = self._trie
        best = 0
        for i in range(start, len(clusters)):
            next_node = node.get(clusters[i])
            if next_node is None:
                break
            node = next_node  # type: ignore[assignment]
            if _END in node:
                best = i - start + 1
        return best


def load_lexicon(*sources: str) -> Lexicon:
    """Load and merge built-in wordlist sources into one lexicon.

    *sources* are keys of :data:`WORD_SOURCES` (``"words"``, ``"names"``,
    ``"modern"``); with no arguments the core ``"words"`` source is loaded.
    Each file is validated independently (duplicates within a file are an
    error); the same entry appearing in several files is merged. Results
    are cached per source combination.

    >>> lex = load_lexicon("words", "names", "modern")
    """
    return _load_lexicon_cached(sources or ("words",))


@cache
def _load_lexicon_cached(sources: tuple[str, ...]) -> Lexicon:
    merged: set[str] = set()
    for source in sources:
        filename = WORD_SOURCES.get(source)
        if filename is None:
            raise ValueError(f"unknown word source {source!r}; available: {sorted(WORD_SOURCES)}")
        if source == "variants":
            # two-column file; the misspellings are what the lexicon matches
            merged |= set(load_variants())
            continue
        text = (resources.files("khmerthings") / "data" / filename).read_text("utf-8")
        merged |= set(Lexicon.from_lines(text.splitlines()))
    return Lexicon(merged)


def _check_khmer_nfc(value: str, role: str, line: str) -> None:
    if unicodedata.normalize("NFC", value) != value:
        raise ValueError(f"{role} is not NFC-normalized in variants line: {line!r}")
    if not all(is_khmer_letter_or_mark(ch) for ch in value):
        raise ValueError(f"{role} contains non-Khmer characters in variants line: {line!r}")


@cache
def load_variants() -> dict[str, str]:
    """Load the built-in misspelling → canonical-spelling map.

    The ``variants.txt`` data file has one mapping per line as
    ``misspelling<TAB>canonical``; blank lines and ``#`` comments are
    ignored. Both columns must be NFC-normalized Khmer text. Duplicate
    misspellings, identity mappings, and canonicals that are themselves
    listed as misspellings are load errors. The returned dict is the
    correction table for spell-fixing; the *keys* double as the
    ``"variants"`` lexicon source for :func:`load_lexicon`.

    >>> load_variants()["ព័ត៍មាន"]
    'ព័ត៌មាន'
    """
    text = (resources.files("khmerthings") / "data" / WORD_SOURCES["variants"]).read_text("utf-8")
    return parse_variants(text.splitlines())


def parse_variants(lines: Iterable[str]) -> dict[str, str]:
    """Parse and validate variant-mapping lines (see :func:`load_variants`)."""
    mapping: dict[str, str] = {}
    for raw in lines:
        line = raw.strip().strip(ZERO_WIDTH_SPACE)
        if not line or line.startswith("#"):
            continue
        variant, sep, canonical = line.partition("\t")
        variant = variant.strip().strip(ZERO_WIDTH_SPACE)
        canonical = canonical.strip().strip(ZERO_WIDTH_SPACE)
        if not sep or not variant or not canonical:
            raise ValueError(f"malformed variants line (want 'variant<TAB>canonical'): {raw!r}")
        _check_khmer_nfc(variant, "variant", raw)
        _check_khmer_nfc(canonical, "canonical", raw)
        if variant == canonical:
            raise ValueError(f"variant maps to itself: {raw!r}")
        if variant in mapping:
            raise ValueError(f"duplicate variant: {variant!r}")
        mapping[variant] = canonical
    for variant, canonical in mapping.items():
        if canonical in mapping:
            raise ValueError(
                f"canonical {canonical!r} (for variant {variant!r}) is itself listed as a variant"
            )
    return mapping


@cache
def load_stopwords() -> dict[str, str]:
    """Load the built-in stopword → category map.

    The ``stopwords.txt`` data file has one entry per line as
    ``word<TAB>category``; blank lines and ``#`` comments are ignored. The
    word must be NFC-normalized Khmer text and the category one of
    :data:`STOPWORD_CATEGORIES`; duplicate words are a load error. The
    returned dict is the classification table for
    :mod:`khmerthings.condense`.

    >>> load_stopwords()["ទេ"]
    'particle'
    """
    text = (resources.files("khmerthings") / "data" / _STOPWORDS_FILE).read_text("utf-8")
    return parse_stopwords(text.splitlines())


def parse_stopwords(lines: Iterable[str]) -> dict[str, str]:
    """Parse and validate stopword-mapping lines (see :func:`load_stopwords`)."""
    mapping: dict[str, str] = {}
    for raw in lines:
        line = raw.strip().strip(ZERO_WIDTH_SPACE)
        if not line or line.startswith("#"):
            continue
        word, sep, category = line.partition("\t")
        word = word.strip().strip(ZERO_WIDTH_SPACE)
        category = category.strip()
        if not sep or not word or not category:
            raise ValueError(f"malformed stopwords line (want 'word<TAB>category'): {raw!r}")
        _check_khmer_nfc(word, "stopword", raw)
        if category not in STOPWORD_CATEGORIES:
            raise ValueError(
                f"unknown stopword category {category!r} (allowed: "
                f"{', '.join(sorted(STOPWORD_CATEGORIES))}) in line: {raw!r}"
            )
        if word in mapping:
            raise ValueError(f"duplicate stopword: {word!r}")
        mapping[word] = category
    return mapping


def default_lexicon() -> Lexicon:
    """The built-in core lexicon (the ``"words"`` source)."""
    return load_lexicon("words")


@cache
def _checking_lexicon(lexicon: Lexicon) -> Lexicon:
    """*lexicon* plus the variant misspellings, so they tokenize as words.

    Shared by :mod:`khmerthings.spellcheck` and :mod:`khmerthings.normalize`,
    which both need known misspellings to surface as single tokens.
    """
    return Lexicon(set(lexicon) | set(load_variants()))
