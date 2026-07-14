"""khmerthings — deterministic Khmer language tools."""

from khmerthings.clusters import segment_clusters
from khmerthings.condense import (
    DEFAULT_REMOVE,
    condense_text,
    content_tokens,
    content_words,
)
from khmerthings.counter import WordCount, analyze, count_words
from khmerthings.lexicon import (
    STOPWORD_CATEGORIES,
    WORD_SOURCES,
    Lexicon,
    default_lexicon,
    load_lexicon,
    load_romanizations,
    load_stopwords,
    load_variants,
)
from khmerthings.normalize import normalize_text, space_sentences, space_words
from khmerthings.numerals import arabic_to_khmer, khmer_to_arabic, number_to_words
from khmerthings.orthography import OrthographyIssue, OrthographyIssueCode, validate_orthography
from khmerthings.romanize import romanize
from khmerthings.segmenter import break_words, mark_boundaries
from khmerthings.sorting import khmer_sort_key, sort_lines
from khmerthings.spellcheck import (
    IssueKind,
    SpellIssue,
    check_spelling,
    check_unknown,
    check_variants,
    fix_spelling,
)
from khmerthings.tokenizer import Token, TokenType, tokenize

__version__ = "0.14.0"

__all__ = [
    "DEFAULT_REMOVE",
    "STOPWORD_CATEGORIES",
    "WORD_SOURCES",
    "IssueKind",
    "Lexicon",
    "OrthographyIssue",
    "OrthographyIssueCode",
    "SpellIssue",
    "Token",
    "TokenType",
    "WordCount",
    "__version__",
    "analyze",
    "arabic_to_khmer",
    "break_words",
    "check_spelling",
    "check_unknown",
    "check_variants",
    "condense_text",
    "content_tokens",
    "content_words",
    "count_words",
    "default_lexicon",
    "fix_spelling",
    "khmer_sort_key",
    "khmer_to_arabic",
    "load_lexicon",
    "load_romanizations",
    "load_stopwords",
    "load_variants",
    "mark_boundaries",
    "normalize_text",
    "number_to_words",
    "romanize",
    "segment_clusters",
    "sort_lines",
    "space_sentences",
    "space_words",
    "tokenize",
    "validate_orthography",
]
