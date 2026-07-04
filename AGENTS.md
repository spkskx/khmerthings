# khmerthings — agent guide

Deterministic Khmer language tools in Python. Note: the repo directory is
`libkhm`, but the package, CLI, and PyPI name is **khmerthings**.

## Hard constraints (non-negotiable)

- **Deterministic only.** Every tool must be rule/algorithm/dictionary-based.
  Same input → same output, always. No probabilistic models, no LLMs, no ML
  inference at runtime.
- **No third-party Khmer NLP code; word data is self-curated.** Do not add
  dependencies on or copy from other Khmer NLP projects, and never
  bulk-import someone else's wordlist. Web research to *find and verify*
  candidate words/names/slang is allowed (user decision, 2026-07-03) — but
  every entry is curated individually and spellings cross-checked.
  **Never document data provenance** — how candidates were found, what
  sources/corpora/tools were used — anywhere in the repo: not in data file
  headers, docs, changelog, or commit messages (user decision, 2026-07-04).
  Data files under `src/khmerthings/data/`:
  `words.txt` (core), `names.txt` (names, surnames, titles), `modern.txt`
  (slang, informal, loanwords, trending), `variants.txt` (misspelling→
  canonical map, two tab-separated columns). All are growable; the word
  files merge via `load_lexicon(*sources)` and the variants map loads via
  `load_variants()` (its keys double as the `variants` lexicon source).
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
3. `lexicon.py` + `data/*.txt` — wordlists (`words`/`names`/`modern`/
   `variants`) + trie keyed by clusters; `longest_match` is the segmentation
   primitive; `load_lexicon(*sources)` merges sources (cached), `--include`
   on the CLI exposes the extra ones; `load_variants()` returns the
   misspelling→canonical map (future spellfixer correction table).
4. `tokenizer.py` — lossless typed tokenization (Khmer words via greedy
   longest-match; unknown Khmer spans become `KHMER_UNKNOWN`, never dropped).
5. `counter.py` — word counter tool (`count_words`, `analyze`).
6. `segmenter.py` — word breaker tool (`break_words`, `mark_boundaries`),
   a thin first-class wrapper over `tokenize`; invariant
   `len(break_words(t)) == count_words(t)`.
7. `sorting.py` — Khmer dictionary-order line sorting (`sort_lines`,
   `khmer_sort_key`: per-cluster key `(base, coengs, vowels, signs)` —
   naive codepoint order is wrong for subscripts).
8. `cli.py` — argparse subcommands, one per tool (`khmerthings count ...`,
   `khmerthings segment ...`, `khmerthings sort ...`).

Planned tools (spellchecker/spellfixer — blocked on lexicon size, POS
tagger, intent detector, paragraph categorizer) follow the same pattern:
new module in `src/khmerthings/`, re-export in `__init__.py`, new CLI
subcommand in `cli.py`, new `tests/test_<module>.py`, and a
**per-tool document `docs/<tool>.md`** (see below).

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
- **Every main (end-user) tool has its own `docs/<tool>.md`** written for
  community users *and for AI agents driving the tools autonomously*,
  following the shared template: What it does / Quick start / CLI
  reference / Python API / How it works / Guarantees & limitations / Task
  recipes / Related tools. Requirements: **every** CLI flag and API
  parameter gets a concrete example with its output; exit codes and error
  output are documented; a "Task recipes" table maps goals → exact
  commands/calls. Low-level primitives are documented via docstrings only,
  not `docs/`. All example outputs must be real — run the command and
  paste the actual output, never invent it (a wrong "expected" output has
  already been caught this way).
- **Update the other docs** touched by the change: `README.md` (landing
  page: tool table, roadmap, examples), the affected `docs/*.md`,
  `DEVELOPMENT_GUIDE.md` (workflow, recipes), docstrings.
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
5. The tag push triggers `.github/workflows/publish.yml`, which re-runs the
   checks, verifies the tag matches `pyproject.toml`, builds, smoke-tests the
   wheel, and publishes to PyPI (needs the `PYPI_API_TOKEN` repo secret,
   configured in repo settings).

## Conventions

- Python ≥ 3.11, mypy `strict`, ruff line length 100.
- Public API re-exported in `__init__.py` with `__all__`; keep `py.typed`.
- Frozen dataclasses for result types (`Token`, `WordCount`).
- Wordlist files (`words.txt`, `names.txt`, `modern.txt`): one entry per
  line, UTF-8, NFC, Khmer letters/marks only, `#` comments, grouped by
  category (no provenance notes). High-frequency words with
  subscript ta/da (្ត/្ដ) spelling variation are listed in both spellings —
  real-world text mixes them. Within a file duplicates are a load error;
  the same entry in different files is fine (merged at load).
- `variants.txt`: one `misspelling<TAB>canonical` mapping per line, for
  clear errors and deprecated orthography only (accepted doubles like ្ត/្ដ
  stay canonical). Tests enforce that every canonical exists in the word
  files and that no variant key is itself a canonical entry (so legitimate
  name spellings such as ចំរើន can never be listed as misspellings).
- Khmer test strings: verify codepoints carefully (visually identical strings
  can differ, e.g. ្ត vs ្ដ); assert exact expected values, hand-verified.
