"""khmerthings — deterministic Khmer language tools."""

from khmerthings.clusters import segment_clusters
from khmerthings.counter import WordCount, analyze, count_words
from khmerthings.lexicon import (
    WORD_SOURCES,
    Lexicon,
    default_lexicon,
    load_lexicon,
    load_variants,
)
from khmerthings.segmenter import break_words, mark_boundaries
from khmerthings.sorting import khmer_sort_key, sort_lines
from khmerthings.spellcheck import IssueKind, SpellIssue, check_spelling, fix_spelling
from khmerthings.tokenizer import Token, TokenType, tokenize

__version__ = "0.7.0"

__all__ = [
    "WORD_SOURCES",
    "IssueKind",
    "Lexicon",
    "SpellIssue",
    "Token",
    "TokenType",
    "WordCount",
    "__version__",
    "analyze",
    "break_words",
    "check_spelling",
    "count_words",
    "default_lexicon",
    "fix_spelling",
    "khmer_sort_key",
    "load_lexicon",
    "load_variants",
    "mark_boundaries",
    "segment_clusters",
    "sort_lines",
    "tokenize",
]
