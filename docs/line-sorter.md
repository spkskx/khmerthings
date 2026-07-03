# Line sorter (`khmerthings sort`)

## What it does

Sorts lines of text in **Khmer dictionary order**, ascending or descending.

Sorting Khmer with plain byte or codepoint comparison (`sort`, Python's
built-in `sorted`) produces wrong orderings, because the *coeng* sign
(U+17D2) that forms subscript consonants has a higher codepoint than every
vowel. A naive sort therefore ranks words by an invisible control character
instead of by how dictionaries order them. This tool sorts the way a Khmer
dictionary does: per character cluster — base consonant first, then
subscript consonants, then vowels, then signs.

Typical uses: sorting wordlists and glossaries, dictionary building,
ordered indexes and reports, deduplication pipelines.

## Quick start

```sh
pip install khmerthings            # library
uv tool install khmerthings       # or: global CLI
```

```sh
$ printf 'ខ្ញុំ\nក្រុម\nការងារ\nApple\n១០០\n' | khmerthings sort
Apple
ការងារ
ក្រុម
ខ្ញុំ
១០០
```

Note ការងារ (vowel form) correctly precedes ក្រុម (subscript form) — a
codepoint sort gets this backwards.

```python
from khmerthings import sort_lines

sort_lines(["ក្រ", "កា", "កក"])
# ['កក', 'កា', 'ក្រ']
```

## CLI reference

```
khmerthings sort [files ...] [--desc]
```

- **`files`** — one or more input files; `-` or no argument reads stdin.
  Multiple files are merged and sorted together (like GNU `sort`).
- **`--desc`** — descending order (the exact reverse of ascending).
- Duplicates are kept. Output is one line per input line.
- Exit code 0 on success.

## Python API

### `sort_lines(lines, *, descending=False) -> list[str]`

Sorts any iterable of strings in Khmer dictionary order and returns a new
list.

```python
from khmerthings import sort_lines

sort_lines(["ខ", "ក", "គ"], descending=True)
# ['គ', 'ខ', 'ក']
```

### `khmer_sort_key(text) -> SortKey`

The underlying collation key, usable anywhere Python accepts a sort key —
so you can order your own data structures by Khmer dictionary order:

```python
from khmerthings import khmer_sort_key

entries.sort(key=lambda e: khmer_sort_key(e.headword))
```

## How it works

Each line is NFC-normalized and split into Khmer character clusters. Every
cluster contributes a comparison tuple
`(base consonant, subscript consonants, vowels, signs)`, which mirrors how
Khmer dictionaries order entries: all vowel forms of a base come before its
subscript stacks, and subscript consonants group with their base instead of
comparing by the coeng codepoint. Non-Khmer characters compare by their
codepoint, so ASCII sorts before Khmer text. The NFC string itself is the
final tiebreaker, making the order total and stable across runs.

This is a practical approximation of Chuon Nath dictionary order, not a
full CLDR/ICU collation (it does not handle e.g. multi-level weighting for
case or width of non-Khmer scripts).

## Guarantees & limitations

- **Deterministic and total.** Same lines, same order, every time —
  regardless of input order (verified by permutation tests).
- **Descending is the exact reverse of ascending.**
- **No dictionary needed.** Unlike the word breaker/counter, sorting is
  purely rule-based; it works identically on any Khmer text with no
  lexicon-coverage caveat.
- Mixed-script lines are supported; non-Khmer text falls back to codepoint
  order rather than locale-aware collation.

## Related tools

- [Word breaker](word-breaker.md) — split Khmer text into words.
- [Word counter](word-counter.md) — count words in Khmer text.
