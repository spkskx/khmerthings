"""khmerthings — deterministic Khmer language tools."""

from khmerthings.clusters import segment_clusters
from khmerthings.counter import WordCount, analyze, count_words
from khmerthings.lexicon import Lexicon, default_lexicon
from khmerthings.sorting import khmer_sort_key, sort_lines
from khmerthings.tokenizer import Token, TokenType, tokenize

__version__ = "0.2.0"

__all__ = [
    "Lexicon",
    "Token",
    "TokenType",
    "WordCount",
    "__version__",
    "analyze",
    "count_words",
    "default_lexicon",
    "khmer_sort_key",
    "segment_clusters",
    "sort_lines",
    "tokenize",
]
