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
from khmerthings.normalize import normalize_text, space_sentences, space_words
from khmerthings.segmenter import break_words, mark_boundaries
from khmerthings.tokenizer import Token, TokenType, tokenize

__version__ = "0.15.1"

__all__ = [
    "WORD_SOURCES",
    "Lexicon",
    "Token",
    "TokenType",
    "WordCount",
    "__version__",
    "analyze",
    "break_words",
    "count_words",
    "default_lexicon",
    "load_lexicon",
    "load_variants",
    "mark_boundaries",
    "normalize_text",
    "segment_clusters",
    "space_sentences",
    "space_words",
    "tokenize",
]
