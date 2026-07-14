# Changelog

All notable changes to khmerthings are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.15.1] - 2026-07-14

### Removed

- Removed line sorting, spell checking/fixing, and orthography validation from
  the top-level Python API, CLI, and public docs. Their modules remain available
  internally, including spelling correction used by normalization.

## [0.15.0] - 2026-07-14

### Removed

- Removed the condenser, romanizer, and numeral converter from the Python API,
  CLI, package data, tests, and documentation. Project scope now focuses on
  segmentation/counting, spelling/normalization, orthography validation, and
  Khmer dictionary-order sorting. The romanizer's internal phonetic rules remain
  private only where needed to rank spelling suggestions.

## [0.14.0] - 2026-07-14

### Added

- Expanded the core lexicon with common complete derived words across `ការ`,
  `ភាព`, `សេចក្តី`/`សេចក្ដី`, `ក្តី`/`ក្ដី`, and `អ្នក` patterns, so
  longest-match tokenization preserves common nominalized and agent compounds.

## [0.13.0] - 2026-07-14

### Added

- Expanded the core lexicon with common complete derived words, including
  `អ្នកស្រែ`, `អ្នករាយការណ៍`, `ការរាយការណ៍`, `ភាពស្អាត`, and both accepted
  spellings of `សេចក្តីស្រឡាញ់`, so longest-match tokenization preserves them.
- **Spellchecker:** unknown-word suggestions now use phonetic similarity and
  NiDA desktop keyboard proximity to break cluster-edit-distance ties before
  Khmer dictionary order. The fixer remains conservative and rewrites only
  curated variants.
- Added a `curl | sh` installer for the `khmerthings` CLI on macOS and Linux.
- Added `khmerthings update` and `khmerthings uninstall` package-management commands;
  they route through the detected installer (`uv tool`, `pipx`, or `pip`), with uninstall
  requiring confirmation.
- **Orthography validator:** `validate_orthography()` and `khmerthings validate`
  report definite Khmer Unicode structure errors with stable issue codes and NFC
  offsets. Validation is deterministic, conservative, read-only, and available
  as plain text or JSON (`--json`; exit 1 when issues are found).

### Fixed

- **Character clusters:** coeng now forms a subscript only with a consonant;
  an independent vowel after coeng starts a new cluster while malformed text
  remains lossless.

## [0.12.0] - 2026-07-10

### Changed

- **Roadmap: the deterministic tool surface is now considered complete and
  frozen.** Focus shifts to consolidation — data depth and correctness
  hardening — rather than new tools. Intent detection and paragraph
  categorization, previously listed as future tools, are **removed from the
  roadmap**: like a POS tagger, they would require probabilistic inference and
  conflict with the determinism guarantee. No code or public API changes.

### Fixed

- **Romanizer:** corrected two common stop+sonorant words the rule engine got
  wrong (it derives register from the last onset consonant, so the sonorant
  wrongly flips the series): `ក្រុង` now romanizes as `krong` (was `krung`) and
  `ប្រាំ` as `pram` (was `bream`), via curated `data/romanize.txt` exceptions.
- **Word breaker:** whole words that were missing from the lexicon no longer
  fragment into shorter matches (the segmenter uses greedy longest-match, so
  segmentation quality is bounded by lexicon coverage — this was a data gap,
  not an algorithm bug). Added the missing entries, e.g. `គូស`, `ហួស`,
  `យោងតាម`, `ឧតុនិយម`, `អាជីវកម្ម`, `ផលវិបាក`, `អវិជ្ជមាន`, `បាក់ច្រាំង`,
  `ហានិភ័យ`, `ជាតិ`, `កត្តា`, `អគ្គនាយកដ្ឋាន` (batch-5 vocabulary), so they now
  segment as single words.

### Development

- Added a coverage-gap harness (`scripts/coverage_gaps.py`): reports the
  `KHMER_UNKNOWN` spans in arbitrary text, ranked by frequency, as an
  evidence-driven backlog for wordlist curation.
- Added a hot-path benchmark (`scripts/benchmark.py`) timing cluster
  segmentation, longest-match tokenization, and edit-distance spell checking,
  as a baseline guard for any future optimization.
- Expanded regression coverage: a broad known-answer table for the romanizer's
  rule engine (initials, dependent vowels per register, codas, signs,
  subscripts, independent vowels), whole-file data-integrity checks over every
  `data/*.txt` file, and cross-file invariants (stopwords are real words,
  variant keys are not stopwords).

## [0.11.0] - 2026-07-08

### Added

- **Romanizer** (`khmerthings romanize` / `romanize`): phonetic UNGEGN-style
  romanization of Khmer into Latin, using a register-aware (1st/2nd series)
  rule engine over character clusters plus a curated whole-word exception
  lexicon (`data/romanize.txt`, loaded by `load_romanizations()`). Phonetic
  and not reversible. `docs/romanize.md`.
- **Numerals** (`khmerthings numerals` with `--to {khmer,arabic,words}` /
  `arabic_to_khmer`, `khmer_to_arabic`, `number_to_words`): Khmer⇄Arabic
  digit conversion (reversible on the digit subset) and spelling integers out
  in Khmer words via the decimal-unit system. `docs/numerals.md`.

## [0.10.0] - 2026-07-07

### Added

- `check_variants` and `check_unknown` in `spellcheck.py`: the two detection
  algorithms `check_spelling` already ran, now independently callable.
- `--only {variants,unknown}` on `khmerthings spellcheck` to run a single
  detection kind.
- `space_words` and `space_sentences` in `normalize.py`: the word-boundary/
  whitespace pass and the Khmer sentence-stop spacing pass, now independently
  callable. `space_sentences` is a pure, lexicon-free string scan.
- `--only {words,sentences}` on `khmerthings normalize` to run a single pass.
- README link to the online demo (https://spkskx.github.io/khmerthings-demo/).

### Changed

- `check_spelling` is now a thin wrapper merging `check_variants` and
  `check_unknown`, sorted by position; behavior and output are unchanged.
- `normalize_text` is now a composition of `spellcheck.fix_spelling`,
  `space_words`, and `space_sentences`; it no longer duplicates the
  variant-fix rule inline. Behavior and output are unchanged.

## [0.9.0] - 2026-07-07

### Added

- Condenser tool (`condense.py`): `content_words()` / `condense_text()` /
  `content_tokens()` strip function words (stopwords) from text, keeping only
  content (meaning-bearing) words — the content-extraction stage for
  downstream intent analysis. Backed by a new curated `stopwords.txt` data
  file (`word<TAB>category`, nine categories) and `load_stopwords()` /
  `STOPWORD_CATEGORIES` in `lexicon.py`. Removes the low-information
  categories by default (`DEFAULT_REMOVE`: particle, politeness, filler,
  preposition, conjunction, demonstrative) and keeps the intent-bearing ones
  (pronoun, auxiliary, question) unless asked; tunable via `remove=` /
  `--remove`. New CLI subcommand `khmerthings condense` (files/stdin,
  `--words`, `--remove`, `--include`). Lossy by design — the only
  khmerthings tool that does not reproduce its input. Documented in
  `docs/condense.md`.
- Stoplist coverage for common function words found in real news/chat text:
  `របស់`, `នៃ` (prepositions); `ក៏`, `ត្រឹម`, `ប៉ុណ្ណោះ`, `ផងដែរ`, `តើ`
  (particles).
- Lexicon additions for the stoplist: `ម្តេច`, `តើ` (words), `អញ្ចឹង`, `ចឹង`
  (modern colloquial fillers).
- Community health files: `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`,
  `SECURITY.md`, and GitHub issue templates (bug report, feature request,
  wordlist addition) under `.github/ISSUE_TEMPLATE/`.

## [0.8.0] - 2026-07-04

### Added

- Normalizer tool (`normalize.py`): `normalize_text()` combines the
  spellfixer's variant corrections with segmentation-aware spacing —
  inserting a hidden zero-width space at bare Khmer word boundaries (same
  rule as `mark_boundaries`), collapsing/trimming ordinary whitespace, and
  tidying spacing around Khmer sentence stops (។, ៕: no space before, one
  space after) — into a single, idempotent, deterministic pass. New CLI
  subcommand `khmerthings normalize` (files/stdin, `--include`, same
  conventions as the other tools). Documented in `docs/normalize.md`.
- New `chars.is_khmer_sentence_stop()` primitive (។ khan, ៕ bariyoosan).

## [0.7.0] - 2026-07-04

### Added

- Spellchecker & spellfixer tool (`spellcheck.py`): `check_spelling()`
  reports `SpellIssue`s — known misspellings from the variants map
  (`IssueKind.VARIANT`, canonical spelling as the suggestion) and
  dictionary-unknown Khmer spans (`IssueKind.UNKNOWN`, suggestions ranked
  by cluster-level edit distance then Khmer dictionary order) — with exact
  NFC offsets; `fix_spelling()` rewrites known misspellings to their
  canonical spelling and never touches anything else. New CLI subcommands
  `khmerthings spellcheck` (grep-style or `--json` output,
  `--max-suggestions`, `--include`; exits 1 when issues are found) and
  `khmerthings spellfix`. Detection and suggestions are pure dictionary
  lookups, so both improve automatically as the wordlists and variants map
  grow. Documented in `docs/spellcheck.md` and `docs/spellfix.md`.

## [0.6.0] - 2026-07-04

### Added

- New `variants` wordlist source: common misspellings mapped to their
  canonical spelling (`variants.txt`, format `misspelling<TAB>canonical`).
  `load_variants()` returns the mapping (the future spellchecker/spellfixer
  correction table); `load_lexicon(..., "variants")` and CLI
  `--include variants` match the misspellings during
  counting/segmentation. 13 seed mappings (e.g. ព័ត៍មាន→ព័ត៌មាន,
  អោយ→ឱ្យ, deprecated ំរ spellings like សំរាប់→សម្រាប់). Accepted
  real-world doubles (្ត/្ដ, ro-ordering) remain canonical, and a spelling
  that is a legitimate name (ចំរើន) is never listed as a variant — both
  enforced by tests.
- Lexicon batch 4: 280 hand-curated general-vocabulary entries in
  `words.txt` (everyday and craft verbs, household objects, body parts,
  nature, kinship, feelings, animals, adjectives/adverbs), with ្ត/្ដ
  doubles where applicable. 1,895 merged canonical entries.
- 41 lexicon entries fixing greedy-segmentation errors where a short name
  entry shadowed the start of a longer word (e.g. សំបុត្រ, សេរីភាព, គណនី,
  លីត្រ, ប្រមាណ, សមាគម), plus missing function words (ទី, ដ៏, ឱកាស, រីឯ) and
  common -ដ្ឋាន compounds (មូលដ្ឋាន, ការដ្ឋាន, អាកាសយានដ្ឋាន).

### Changed

- មិនា and សំអាត moved from `words.txt` to `variants.txt` (canonical
  spellings: មីនា, សម្អាត).

## [0.5.0] - 2026-07-04

### Added

- Lexicon batch 3: 784 new hand-curated, individually verified entries —
  `words.txt` 610 → 1,216 lines, `names.txt` 212 → 405, `modern.txt`
  44 → 66 (1,583 merged entries, up from 802). Includes all 12 month names,
  days of the week, countries and world cities, all 25 Cambodian provinces
  plus common districts, government and news vocabulary (with real-world
  spelling variants such as រដ្ឋមន្ត្រី/រដ្ឋមន្រ្តី and ្ត/្ដ pairs), Khmer
  surnames and given names, and transliterated foreign public figures.
  Substantially improves word segmentation of real-world news text.

## [0.4.3] - 2026-07-03

### Added

- GitHub Actions publish workflow: pushing a `vX.Y.Z` tag now runs the full
  checks, verifies the tag matches the package version, builds, smoke-tests
  the wheel, and uploads to PyPI (requires the `PYPI_API_TOKEN` secret).

## [0.4.2] - 2026-07-03

### Added

- Lexicon: ខ្សោយ (weak) — reported missing via
  `khmerthings count` showing it as an unknown span.

## [0.4.1] - 2026-07-03

### Changed

- Per-tool docs rewritten for autonomous (AI-agent and scripted) use:
  every CLI flag and Python API parameter now has a concrete example with
  real executed output, exit codes and error output are documented, and
  each doc ends with a "Task recipes" table mapping goals to exact
  commands/calls.

### Fixed

- CLI: a missing/unreadable input file now exits with code 1 and a
  one-line `khmerthings: error: ...` message instead of a Python traceback.

## [0.4.0] - 2026-07-03

### Added

- Two new growable wordlist sources alongside the core vocabulary
  (curated entry by entry, spellings cross-checked):
  - `names.txt` (200 entries): Khmer surnames, given names, and honorific
    titles (ឯកឧត្តម, សម្តេច, …).
  - `modern.txt` (30 entries): slang (ឡូយ, ស្ទាវ), informal register,
    tech/media loanwords (ហ្វេសប៊ុក, អនឡាញ), and everyday modern loanwords.
- `load_lexicon(*sources)` public API: merge any combination of `words`,
  `names`, `modern` (cached, per-file validation, cross-file duplicates
  merged); `WORD_SOURCES` lists the available sources.
- `--include names,modern` flag on `khmerthings count` and
  `khmerthings segment` to match against the extra wordlists.

### Changed

- Data policy clarified: all word data is self-curated entry by entry;
  bulk-importing third-party wordlists remains forbidden.
- Total curated entries: 802 across the three sources.

## [0.3.0] - 2026-07-03

### Added

- Word breaker tool: `khmerthings.segmenter` with `break_words(text)`
  (words as a list; length always equals `count_words`) and
  `mark_boundaries(text, separator="​")` (insert separators at Khmer
  word boundaries, everything else preserved).
- `khmerthings segment [files|-] [--separator SEP] [--mark]` CLI subcommand.
- Per-tool community documentation in `docs/`: `word-breaker.md`,
  `word-counter.md`, `line-sorter.md` — each with quick start, CLI and
  Python API reference, how-it-works, and guarantees/limitations. All
  example outputs are real, executed outputs.
- Lexicon batch 2: +290 hand-curated words (family & occupations, food &
  drink, verbs, adjectives, connectives, society & learning, time & places);
  now 582 words.

### Changed

- `README.md` restructured as a community landing page: tool table linking
  to per-tool docs, roadmap (spellchecker/spellfixer next, pending lexicon
  coverage), contributing pointers.
- Doc-upkeep rules in `AGENTS.md`/`DEVELOPMENT_GUIDE.md`/PR template now
  require a `docs/<tool>.md` for every main tool, with verified outputs.

## [0.2.0] - 2026-07-03

### Added

- Khmer dictionary-order line sorting: `khmerthings.sorting` module with
  `sort_lines(lines, descending=False)` and `khmer_sort_key(text)` (a
  collation key usable directly with `sorted()`). Sorting is per character
  cluster — base consonant, then subscript consonants, then dependent
  vowels, then signs — approximating Chuon Nath dictionary order, which
  naive codepoint sorting gets wrong for subscript consonants.
- `khmerthings sort [files|-] [--desc]` CLI subcommand (stdin by default,
  multiple files merged).
- `CHANGELOG.md` (this file) and documentation-upkeep rules in `AGENTS.md`.

## [0.1.0] - 2026-07-03

### Added

- Initial release: deterministic Khmer language toolkit with zero runtime
  dependencies, built from first principles.
- `khmerthings.chars`: Khmer Unicode character classification (consonants,
  vowels, signs, coeng, digits, punctuation, script classes).
- `khmerthings.clusters`: Khmer character-cluster (KCC) segmentation with a
  losslessness invariant (never drops or reorders characters).
- `khmerthings.lexicon`: hand-curated seed lexicon (~290 words) with
  trie-based longest-match lookup keyed by clusters.
- `khmerthings.tokenizer`: lossless typed tokenization of mixed
  Khmer/Latin text; unknown Khmer spans preserved as `KHMER_UNKNOWN`.
- `khmerthings.counter`: word counter (`count_words`, `analyze`) aware that
  Khmer writes no spaces between words.
- `khmerthings count [files|-] [--json]` CLI, installable globally.
- Full test suite (207 tests), strict mypy, ruff, GitHub Actions CI
  (lint, Python 3.11–3.14 test matrix, build + wheel smoke test), MIT
  license, AGENTS.md/CLAUDE.md, DEVELOPMENT_GUIDE.md, PR template.

[0.7.0]: https://github.com/spkskx/khmerthings/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/spkskx/khmerthings/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/spkskx/khmerthings/compare/v0.4.3...v0.5.0
[0.4.3]: https://github.com/spkskx/khmerthings/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/spkskx/khmerthings/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/spkskx/khmerthings/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/spkskx/khmerthings/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/spkskx/khmerthings/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/spkskx/khmerthings/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/spkskx/khmerthings/releases/tag/v0.1.0
