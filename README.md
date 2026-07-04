# khmerthings

Deterministic Khmer language tools for Python — built as **community
building blocks**: small, correct, dependency-free primitives you can
compose into bigger systems.

No machine-learning models, no third-party NLP dependencies, no network
calls. Every result is reproducible and explainable. Khmer script writes no
spaces between words, so even "simple" operations like counting or sorting
need real language handling — khmerthings implements that from first
principles.

## Tools

Each tool is available both as a Python API and a CLI subcommand, and has
its own detailed document:

| Tool | CLI | Python | Docs |
|---|---|---|---|
| **Word breaker** — split Khmer text into words | `khmerthings segment` | `break_words`, `mark_boundaries` | [docs/word-breaker.md](docs/word-breaker.md) |
| **Word counter** — count words in Khmer/mixed text | `khmerthings count` | `count_words`, `analyze` | [docs/word-counter.md](docs/word-counter.md) |
| **Line sorter** — Khmer dictionary-order sorting | `khmerthings sort` | `sort_lines`, `khmer_sort_key` | [docs/line-sorter.md](docs/line-sorter.md) |
| **Spellchecker** — find Khmer misspellings & unknown words | `khmerthings spellcheck` | `check_spelling` | [docs/spellcheck.md](docs/spellcheck.md) |
| **Spellfixer** — rewrite known misspellings to canonical | `khmerthings spellfix` | `fix_spelling` | [docs/spellfix.md](docs/spellfix.md) |
| **Normalizer** — spellfix + re-space into clean, ready-to-use text | `khmerthings normalize` | `normalize_text` | [docs/normalize.md](docs/normalize.md) |

## Install

```sh
pip install khmerthings          # library
uv tool install khmerthings     # global CLI
```

## A taste

```sh
$ echo "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ" | khmerthings segment
ខ្ញុំ ស្រឡាញ់ ភាសា ខ្មែរ
```

```python
from khmerthings import break_words, count_words, fix_spelling, sort_lines

break_words("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ")   # ['ខ្ញុំ', 'ស្រឡាញ់', 'ភាសា', 'ខ្មែរ']
count_words("ខ្ញុំមានឆ្កែ ២ ក្បាល and 3 cats")   # 8
sort_lines(["ក្រ", "កា", "កក"])                    # ['កក', 'កា', 'ក្រ']
fix_spelling("ខ្ញុំសំរាប់ការងារ")                  # 'ខ្ញុំសម្រាប់ការងារ'
```

## Design principles

- **Deterministic**: same input, same output, always. Rule- and
  dictionary-based algorithms only; nothing probabilistic.
- **Self-contained**: zero runtime dependencies; all word data is our own
  hand-curated set of growable wordlists — `words` (core vocabulary),
  `names` (people's names & titles), `modern` (slang, loanwords, trending
  terms), and `variants` (common misspellings mapped to their canonical
  spelling) — 1,895 entries and growing, each verified entry by entry; no
  wordlist is imported wholesale.
- **Lossless**: no character is ever dropped — unknown Khmer spans are
  reported, not discarded.
- **Tested first**: every module ships with table-driven unit tests and
  invariant checks (332 tests and growing).

Under the hood, the tools share deterministic primitives (character
classification, character-cluster segmentation, a cluster-keyed lexicon
trie, lossless tokenization) in `src/khmerthings/` — see the module
docstrings if you want to build on them directly.

## Roadmap

- ✅ Word counter, line sorter, word breaker, spellchecker & spellfixer,
  normalizer
- ⏳ Wordlist growth across all four sources (`words`, `names`, `modern`,
  `variants`) — hand-curated batches each release; the accuracy lever for
  every dictionary-based tool, including the spellchecker's verdicts,
  suggestions, and fixes
- Later: part-of-speech tagger, intent detection, paragraph categorization

## Contributing

See [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for setup, the
architecture, the rules (determinism, self-owned data, tests first), and
how to add words to the lexicon — the single most valuable contribution.
Changes are tracked in [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE)
