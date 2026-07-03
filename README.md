# khmerthings

Deterministic Khmer language tools for Python. No machine-learning models, no
third-party NLP dependencies — every result is reproducible and explainable.

Khmer script has no spaces between words, so even counting words requires
real segmentation. khmerthings builds that from first principles:

- **Character classification** (`khmerthings.chars`) — Khmer Unicode block predicates.
- **Character-cluster segmentation** (`khmerthings.clusters`) — splits text into
  Khmer character clusters (KCC), the atomic units of the script.
- **Lexicon** (`khmerthings.lexicon`) — a hand-curated wordlist with trie-based
  longest-match lookup.
- **Tokenizer** (`khmerthings.tokenizer`) — lossless, typed tokenization of mixed
  Khmer/Latin text.
- **Word counter** (`khmerthings.counter`) — the first end-user tool.
- **Line sorter** (`khmerthings.sorting`) — sorts lines in Khmer dictionary
  order (naive codepoint sorting gets subscript consonants wrong).

More tools (word breaker, spellchecker, POS tagger, …) will build on the same
primitives.

## Install

```sh
pip install khmerthings          # library
uv tool install khmerthings     # global CLI
```

## Library usage

```python
from khmerthings import count_words, analyze, tokenize, segment_clusters

count_words("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ")   # 4

stats = analyze("ខ្ញុំមានឆ្កែ ២ ក្បាល and 3 cats")
stats.total_words        # 8
stats.khmer_words        # 4
stats.latin_words        # 2
stats.numbers            # 2

segment_clusters("ខ្ញុំស្រឡាញ់")   # ['ខ្ញុំ', 'ស្រ', 'ឡា', 'ញ់']

from khmerthings import sort_lines, khmer_sort_key
sort_lines(["ក្រ", "កា", "កក"])              # ['កក', 'កា', 'ក្រ'] — dictionary order
sort_lines(["ខ", "ក"], descending=True)      # ['ខ', 'ក']
sorted(words, key=khmer_sort_key)             # use the collation key directly
```

## CLI usage

```sh
khmerthings count file.txt
echo "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ" | khmerthings count
khmerthings count --json file.txt
khmerthings sort file.txt           # sort lines in Khmer dictionary order
khmerthings sort --desc file.txt    # descending
```

## Design principles

- **Deterministic**: same input, same output, always. Rule- and
  dictionary-based algorithms only; nothing probabilistic.
- **Self-contained**: zero runtime dependencies; the lexicon is our own
  hand-curated data, grown over time.
- **Lossless**: tokenization never drops characters — unknown Khmer spans are
  reported as `KHMER_UNKNOWN` tokens, not discarded.
- **Tested first**: the test suite is the primary artifact; every module ships
  with table-driven unit tests and invariant checks.

## Development

```sh
uv sync                 # create env, install dev deps
uv run pytest           # tests
uv run mypy src tests   # type check
uv run ruff check       # lint
uv run ruff format      # format
```
