# khmerthings — agent guide

Deterministic Khmer language tools in Python. Note: the repo directory is
`libkhm`, but the package, CLI, and PyPI name is **khmerthings**.

## Hard constraints (non-negotiable)

- **Deterministic only.** Every tool must be rule/algorithm/dictionary-based.
  Same input → same output, always. No probabilistic models, no LLMs, no ML
  inference at runtime.
- **No third-party Khmer NLP code or data.** Do not add dependencies on or
  copy from other Khmer NLP projects. The lexicon
  (`src/khmerthings/data/words.txt`) is hand-curated, self-owned data — grow
  it, never import a wordlist.
- **Zero runtime dependencies.** Stdlib only. Dev tools (pytest, ruff, mypy)
  are the only allowed dependencies.
- **Tests are the top priority.** Every module ships with table-driven unit
  tests and invariant checks. Write/update tests with every change.

## Commands

```sh
uv sync                      # env + dev deps
uv run pytest                # tests (must stay green)
uv run mypy src tests        # strict mode, must be clean
uv run ruff check --fix && uv run ruff format
uv build                     # sdist + wheel
echo "ខ្មែរ" | uv run khmerthings count   # CLI smoke test
```

Run all four checks (pytest, mypy, ruff check, ruff format --check) before
considering any change done.

## Architecture

`src/` layout; modules build bottom-up, each layer a primitive for the next:

1. `chars.py` — Khmer Unicode character classification (pure functions,
   single-character contract: multi-char input raises `ValueError`).
2. `clusters.py` — Khmer character-cluster (KCC) segmentation. Cluster
   boundaries are the only legal word boundaries.
3. `lexicon.py` + `data/words.txt` — wordlist + trie keyed by clusters;
   `longest_match` is the segmentation primitive.
4. `tokenizer.py` — lossless typed tokenization (Khmer words via greedy
   longest-match; unknown Khmer spans become `KHMER_UNKNOWN`, never dropped).
5. `counter.py` — word counter tool (`count_words`, `analyze`).
6. `sorting.py` — Khmer dictionary-order line sorting (`sort_lines`,
   `khmer_sort_key`: per-cluster key `(base, coengs, vowels, signs)` —
   naive codepoint order is wrong for subscripts).
7. `cli.py` — argparse subcommands, one per tool (`khmerthings count ...`,
   `khmerthings sort ...`).

Planned tools (word breaker, spellchecker, POS tagger, intent detector,
paragraph categorizer) follow the same pattern: new module in
`src/khmerthings/`, re-export in `__init__.py`, new CLI subcommand in
`cli.py`, new `tests/test_<module>.py`.

## Invariants to preserve (enforced by tests)

- `"".join(segment_clusters(t)) == unicodedata.normalize("NFC", t)` — cluster
  segmentation never drops or reorders characters, even on malformed input.
- Tokenization is lossless: concatenated token texts equal the NFC input, and
  token offsets are contiguous.
- All text is NFC-normalized at entry points; lexicon entries must be NFC,
  Khmer-letters-only, and unique (loader raises otherwise).
- A lexicon match can never split a character cluster.

## Documentation upkeep (do this every change)

Docs must always reflect the current state of the code. As part of any
change — not as an afterthought:

- **Self-update this file (AGENTS.md)** when architecture, constraints,
  commands, tools, or conventions change (e.g. a new module or subcommand).
- **Update the other docs** touched by the change: `README.md` (features,
  usage examples, CLI), `DEVELOPMENT_GUIDE.md` (workflow, recipes),
  docstrings.
- **Keep `CHANGELOG.md` current**: add an entry under `[Unreleased]` for
  every user-visible change (Keep a Changelog format: Added / Changed /
  Fixed / Removed). On release, rename `[Unreleased]` to the version + date.
- A PR that changes behavior but touches no docs/changelog is incomplete —
  the PR template checklist enforces this.

## Releasing

1. Bump `version` in `pyproject.toml` **and** `__version__` in
   `src/khmerthings/__init__.py` (they must stay in sync).
2. Turn the `[Unreleased]` section of `CHANGELOG.md` into `[X.Y.Z] - date`.
3. `uv sync` (refresh lockfile), run all four checks, commit.
4. `git tag vX.Y.Z && git push origin main --tags`.

## Conventions

- Python ≥ 3.11, mypy `strict`, ruff line length 100.
- Public API re-exported in `__init__.py` with `__all__`; keep `py.typed`.
- Frozen dataclasses for result types (`Token`, `WordCount`).
- `words.txt`: one word per line, UTF-8, NFC, `#` comments, grouped by
  category. High-frequency words with subscript ta/da (្ត/្ដ) spelling
  variation are listed in both spellings — real-world text mixes them.
- Khmer test strings: verify codepoints carefully (visually identical strings
  can differ, e.g. ្ត vs ្ដ); assert exact expected values, hand-verified.
