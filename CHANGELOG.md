# Changelog

All notable changes to khmerthings are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-07-03

### Added

- Two new growable wordlist sources alongside the core vocabulary
  (candidates researched from public sources — Wikipedia's Cambodian-name
  article, Behind the Name, Khmer Wiktionary and Khmer media — and curated
  entry by entry, spellings cross-checked):
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

- Data policy clarified: web research to find/verify candidate entries is
  allowed; bulk-importing third-party wordlists remains forbidden. Sources
  are noted in each data file header.
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

[Unreleased]: https://github.com/spkskx/khmerthings/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/spkskx/khmerthings/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/spkskx/khmerthings/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/spkskx/khmerthings/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/spkskx/khmerthings/releases/tag/v0.1.0
