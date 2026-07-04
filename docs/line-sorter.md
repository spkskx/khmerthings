# Line sorter (`khmerthings sort`)

## What it does

Sorts lines of text in **Khmer dictionary order**, ascending or descending.

Sorting Khmer with plain byte or codepoint comparison (GNU `sort`, Python's
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

Every option, with a real example of its effect:

### Input: files, multiple files, or stdin

`files` is zero or more paths; `-` or no argument reads stdin. Multiple
files are **merged and sorted together** (like GNU `sort`), one output line
per input line; duplicates are kept:

```sh
$ khmerthings sort a.txt b.txt        # 3 lines across 2 files, merged
ខ្ញុំស្រឡាញ់ភាសាខ្មែរ
ថ្ងៃនេះខ្ញុំទៅផ្សារ
សួស្តី SokSan!
```

### `--desc` — descending order

The exact reverse of the ascending order:

```sh
$ printf 'ខ្មៅ\nក្រហម\nស\nបៃតង\n' | khmerthings sort --desc
ស
បៃតង
ខ្មៅ
ក្រហម
```

### Exit codes & errors

- `0` — success.
- `1` — an input file could not be read; one-line message on stderr:
  `khmerthings: error: [Errno 2] No such file or directory: '...'`
- `2` — bad usage (unknown flag).

No dictionary is involved — `sort` has no `--include` flag; it works
identically on any Khmer text.

## Python API

### `sort_lines(lines, *, descending=False) -> list[str]`

Sorts any iterable of strings in Khmer dictionary order and returns a new
list. Duplicates are kept; the input is not modified.

```python
from khmerthings import sort_lines

sort_lines(["ខ", "ក", "គ"])                      # ['ក', 'ខ', 'គ']
sort_lines(["ខ", "ក", "គ"], descending=True)     # ['គ', 'ខ', 'ក']
sort_lines(["ខ្មែរ", "english", "ការងារ"])        # ['english', 'ការងារ', 'ខ្មែរ']
sort_lines([])                                    # []
```

Deduplicate by passing a set:

```python
sort_lines({"ក", "ខ", "ក"})
# ['ក', 'ខ']
```

### `khmer_sort_key(text) -> SortKey`

The underlying collation key — usable anywhere Python accepts a `key=`
callable, so you can order *any* data structure by Khmer dictionary order:

```python
from khmerthings import khmer_sort_key

cities = ["ភ្នំពេញ", "កំពត", "បាត់ដំបង", "សៀមរាប"]

sorted(cities, key=khmer_sort_key)
# ['កំពត', 'បាត់ដំបង', 'ភ្នំពេញ', 'សៀមរាប']

min(cities, key=khmer_sort_key)       # 'កំពត'
max(cities, key=khmer_sort_key)       # 'សៀមរាប'

entries.sort(key=lambda e: khmer_sort_key(e.headword))   # objects
dict(sorted(d.items(), key=lambda kv: khmer_sort_key(kv[0])))  # dict by key
```

Keys are ordinary tuples: comparable with `<`/`>`, safe to use in
`bisect`, heaps, or as pandas sort keys via `.map(khmer_sort_key)`.

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
  purely rule-based; there is no lexicon-coverage caveat.
- Mixed-script lines are supported; non-Khmer text falls back to codepoint
  order (so `Z` < `a`, and all ASCII < Khmer) rather than locale-aware
  collation.

## Task recipes

| Goal | Do this |
|---|---|
| Sort a file of Khmer lines | `khmerthings sort file.txt` |
| Sorted, deduplicated wordlist | `sort_lines(set(lines))` or `khmerthings sort f.txt \| uniq` |
| Sort your own objects by a Khmer field | `sorted(objs, key=lambda o: khmer_sort_key(o.field))` |
| Alphabetical min/max | `min(words, key=khmer_sort_key)` |
| Merge + sort many files | `khmerthings sort a.txt b.txt c.txt` |
| Reverse (Z→A style) listing | `--desc` / `descending=True` |

## Related tools

- [Word breaker](word-breaker.md) — split Khmer text into words (e.g. to
  produce the lines you sort).
- [Word counter](word-counter.md) — count words in Khmer text.
- [Spellchecker](spellcheck.md) — uses this collation to rank its
  suggestions.
