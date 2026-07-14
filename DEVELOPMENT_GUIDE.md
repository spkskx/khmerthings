# Development guide

How to work on khmerthings. Agent-oriented rules live in [AGENTS.md](AGENTS.md);
this guide is for humans. The short version: deterministic algorithms only,
self-owned data only, and tests come first.

## Setup

Requires [uv](https://docs.astral.sh/uv/). Python 3.11+ is provisioned
automatically.

```sh
git clone git@github.com:spkskx/khmerthings.git
cd khmerthings
uv sync          # creates .venv with dev dependencies
```

## Everyday commands

```sh
uv run pytest                          # run the test suite
uv run pytest tests/test_clusters.py  # one file
uv run mypy src tests                  # type check (strict)
uv run ruff check --fix                # lint (+autofix)
uv run ruff format                     # format
uv run khmerthings count file.txt      # run the CLI from source
uv build                               # build sdist + wheel
```

All of pytest, mypy, `ruff check`, and `ruff format --check` must pass before
a change is done — CI enforces exactly these on every PR.

## Branching & PRs

- `main` is the only long-lived branch and is what CI, tags, and releases
  point at. Work on short-lived feature branches and open a PR into `main`.
- CI runs lint/type checks, the test matrix (Python 3.11–3.14), a package
  build, and a wheel smoke test. All jobs must be green to merge.
- Keep `uv.lock` committed; CI installs with `uv sync --locked`.

## Project rules

1. **Deterministic only.** Same input → same output, always. Dictionary- and
   rule-based algorithms; no ML inference, no LLMs, no randomness.
2. **Self-owned everything.** No third-party Khmer NLP libraries and no
   bulk-imported wordlists/corpora. Word data is hand-curated entry by
   entry in `src/khmerthings/data/` — web research to find and verify
   candidates is fine; copying someone's wordlist wholesale is not. Do not
   document data provenance (sources, corpora, tooling) anywhere in the repo.
3. **Zero runtime dependencies.** Stdlib only; dev tooling is the only
   exception.
4. **Tests first.** Every behavior change comes with tests. Prefer
   table-driven `pytest.mark.parametrize` cases plus invariant tests (see
   `tests/test_clusters.py::TestInvariants` for the pattern).

## Adding a new tool

The deterministic tool surface is complete and frozen — the current phase is
consolidation, not new tools, and semantic tools (intent, categorization, POS)
are out of scope (they'd need probabilistic inference). This section stays as
the reference for the rare case of adding another *deterministic* tool.

Follow the existing bottom-up architecture (chars → clusters → lexicon →
tokenizer → tools). To add a tool, e.g. a hypothetical `foo`:

1. Create `src/khmerthings/foo.py`, building on the existing
   primitives (`segment_clusters`, `Lexicon.longest_match`, `tokenize`,
   and — for meaning-only input — `content_words`).
2. Re-export the public API in `src/khmerthings/__init__.py` (`__all__`).
3. Add a CLI subcommand in `src/khmerthings/cli.py` (`khmerthings foo`).
4. Add `tests/test_foo.py` with unit + invariant tests.
5. Write its per-tool document `docs/foo.md` following the shared
   template used by the existing docs (What it does / Quick start / CLI
   reference / Python API / How it works / Guarantees & limitations /
   Related tools). All example outputs must be real, verified outputs.
6. Add it to the tool table and roadmap in `README.md`, and to `AGENTS.md`.

## Editing the wordlists (`src/khmerthings/data/`)

Five growable files. The first four merge on demand via
`load_lexicon(*sources)`; `stopwords.txt` loads separately via
`load_stopwords()`:

| File | Source name | Contents |
|---|---|---|
| `words.txt` | `words` | core vocabulary (always loaded) |
| `names.txt` | `names` | personal names, surnames, honorific titles |
| `modern.txt` | `modern` | slang, informal register, loanwords, trending terms |
| `variants.txt` | `variants` | common misspellings → canonical spelling (two columns) |
| `stopwords.txt` | — | function words → category, for the condenser (two columns); every word must also exist in the word files |
| `romanize.txt` | — | Khmer word → Latin spelling, for the romanizer (two columns); key is NFC Khmer, value is ASCII |

Put new entries in the right file: standard dictionary vocabulary → `words`;
anything people are called → `names`; register that shifts with time
(slang, borrowings, internet vocabulary) → `modern`; clear misspellings and
deprecated orthography → `variants` (format `misspelling<TAB>canonical`;
the canonical form must exist in the other files, and a spelling that is a
legitimate name — e.g. ចំរើន — must not be listed as a variant; both rules
are enforced by tests). Accepted real-world doubles (subscript ta/da ្ត/្ដ,
ro-ordering pairs) are *not* variants; list both spellings as canonical.

- One entry per line, UTF-8, NFC-normalized, Khmer letters/marks only —
  the loader rejects anything else (including within-file duplicates) at
  load time. The same entry may appear in different files (merged at load).
- Keep entries in their category section; add a new `# --- section ---` when
  needed. Do not note research sources or provenance in the files.
- Words with subscript ta/da (្ត/្ដ) spelling variation should be added in
  **both** spellings — the two render identically and real text mixes them.
- Beware visually identical strings with different codepoints; verify with
  `python -c "print([hex(ord(c)) for c in 'word'])"` when in doubt.
- Adding words is the highest-leverage accuracy improvement for every tool.

## Khmer script primer (why the code looks like this)

- Khmer writes **no spaces between words**; spaces separate phrases. Word
  boundaries must be inferred via the lexicon.
- A **character cluster** (base consonant + subscript consonants + vowel +
  signs) is the smallest indivisible unit; word boundaries can only fall on
  cluster boundaries. `clusters.py` finds permissive, lossless boundaries.
- `orthography.py` separately reports definite malformed encoding structures.
  It is conservative and read-only: no dictionary lookup, guessed correction,
  mark reordering, or limit on stacked consonants.
- The zero-width space (U+200B) is used in real Khmer text as an explicit
  word delimiter; the tokenizer treats it as whitespace.

## Documentation & changelog

Docs are part of every change, not a follow-up: update `README.md`,
`AGENTS.md`, `DEVELOPMENT_GUIDE.md`, and docstrings whenever behavior,
architecture, or workflow changes, and add an entry to the `[Unreleased]`
section of `CHANGELOG.md` (Keep a Changelog format) for every user-visible
change. A behavior-changing PR with no docs/changelog update is incomplete.

## Releasing

1. Bump `version` in `pyproject.toml` and `__version__` in
   `src/khmerthings/__init__.py` (keep them in sync).
2. Rename the `[Unreleased]` section of `CHANGELOG.md` to `[X.Y.Z] - date`
   and update the compare links at the bottom.
3. Update the lockfile: `uv sync`.
4. Commit, then tag: `git tag vX.Y.Z && git push origin main --tags`.
5. Build artifacts with `uv build` (CI also builds and uploads them).
