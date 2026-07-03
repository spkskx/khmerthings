# Changelog

All notable changes to khmerthings are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/spkskx/khmerthings/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/spkskx/khmerthings/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/spkskx/khmerthings/releases/tag/v0.1.0
