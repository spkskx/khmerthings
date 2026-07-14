# khmerthings

Deterministic Khmer language tools for Python — built as **community
building blocks**: small, correct, dependency-free primitives you can
compose into bigger systems.

No machine-learning models, no third-party NLP dependencies, no network
calls. Every result is reproducible and explainable. Khmer script writes no
spaces between words, so even "simple" word operations need real language
handling — khmerthings implements that from first
principles.

**[Try it in your browser →](https://spkskx.github.io/khmerthings-demo/)**

## Tools

Each tool is available both as a Python API and a CLI subcommand, and has
its own detailed document:

| Tool | CLI | Python | Docs |
|---|---|---|---|
| **Word breaker** — split Khmer text into words | `khmerthings segment` | `break_words`, `mark_boundaries` | [docs/word-breaker.md](docs/word-breaker.md) |
| **Word counter** — count words in Khmer/mixed text | `khmerthings count` | `count_words`, `analyze` | [docs/word-counter.md](docs/word-counter.md) |
| **Normalizer** — spellfix + re-space into clean, ready-to-use text | `khmerthings normalize` | `normalize_text` | [docs/normalize.md](docs/normalize.md) |

## Install

```sh
pip install khmerthings         # library
uv tool install khmerthings     # global CLI
```

Or install the CLI with one command (installs `uv` first when needed):

```sh
curl -LsSf https://raw.githubusercontent.com/spkskx/khmerthings/main/install.sh | sh
```

Requires macOS or Linux. Verify the install with `khmerthings --help`.

Update or remove the CLI from the same command:

```sh
khmerthings update      # upgrade with uv tool, pipx, or pip (detected from the install)
khmerthings uninstall   # asks y/N, then removes the package the same way
```

## A taste

```sh
$ echo "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ" | khmerthings segment
ខ្ញុំ ស្រឡាញ់ ភាសា ខ្មែរ
```

```python
from khmerthings import break_words, count_words, normalize_text

break_words("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ")   # ['ខ្ញុំ', 'ស្រឡាញ់', 'ភាសា', 'ខ្មែរ']
count_words("ខ្ញុំមានឆ្កែ ២ ក្បាល and 3 cats")   # 8
normalize_text("ខ្ញុំសំរាប់ការងារ")              # 'ខ្ញុំ​សម្រាប់​ការងារ'
```

## Design principles

- **Deterministic**: same input, same output, always. Rule- and
  dictionary-based algorithms only; nothing probabilistic.
- **Self-contained**: zero runtime dependencies; all word data is our own
  hand-curated set of growable wordlists — `words` (core vocabulary),
  `names` (people's names & titles), `modern` (slang, loanwords, trending
  terms), `variants` (common misspellings mapped to their canonical
  spelling) — 1,900+ entries and growing, each verified entry by entry; no wordlist is
  imported wholesale.
- **Lossless**: no character is ever dropped — unknown Khmer spans are
  reported, not discarded.
- **Tested first**: every module ships with table-driven unit tests and
  invariant checks (500+ tests and growing).

Under the hood, the tools share deterministic primitives (character
classification, character-cluster segmentation, a cluster-keyed lexicon
trie, lossless tokenization) in `src/khmerthings/` — see the module
docstrings if you want to build on them directly.

## Roadmap

The deterministic tool surface is **complete and frozen** — the focus now is
depth, not breadth: growing the data and hardening what's already here.

- ✅ Word segmentation, counting, and normalization
- ⏳ Wordlist growth across all four sources (`words`, `names`, `modern`,
  `variants`) — hand-curated batches each release; the accuracy lever for every
  dictionary-based processing
- ⏳ Quality & correctness — known-answer regression suites for segmentation
  and normalization; invariant/edge-case hardening; profiling
  of hot paths

**Out of scope / not planned:** semantic ("understanding-level") NLP that
would require probabilistic models — intent detection, paragraph
categorization, and POS tagging are intentionally *not* on the roadmap. They conflict with the determinism guarantee.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and
[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for setup, the architecture,
the rules (determinism, self-owned data, tests first), and how to add
words to the lexicon — the single most valuable contribution. This project
follows a [Code of Conduct](CODE_OF_CONDUCT.md). Changes are tracked in
[CHANGELOG.md](CHANGELOG.md). Report security issues per
[SECURITY.md](SECURITY.md) rather than in a public issue.

## License

[MIT](LICENSE)
