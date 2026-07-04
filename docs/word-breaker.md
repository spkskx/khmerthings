# Word breaker (`khmerthings segment`)

## What it does

Splits Khmer text into words. Khmer script writes **no spaces between
words** — spaces only separate phrases — so "splitting on whitespace" does
not work for Khmer the way it does for English. The word breaker finds word
boundaries using a dictionary and a deterministic longest-match algorithm,
and returns the result either as a list of words or as the original text
with boundary markers inserted.

This is the foundational operation for almost everything else: search
indexing, line breaking, keyword extraction, text statistics, and machine
learning preprocessing all need Khmer word boundaries first.

## Quick start

```sh
pip install khmerthings            # library
uv tool install khmerthings       # or: global CLI
```

```sh
$ echo "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ" | khmerthings segment
ខ្ញុំ ស្រឡាញ់ ភាសា ខ្មែរ
```

```python
from khmerthings import break_words

break_words("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ")
# ['ខ្ញុំ', 'ស្រឡាញ់', 'ភាសា', 'ខ្មែរ']
```

## CLI reference

```
khmerthings segment [files ...] [--separator SEP] [--mark] [--include modern,names,variants]
```

Every option, with a real example of its effect:

### Input: files, multiple files, or stdin

`files` is zero or more paths; `-` or no argument reads stdin. Each input
line produces one output line, files processed in order:

```sh
$ khmerthings segment a.txt b.txt        # a.txt: two lines, b.txt: one line
ខ្ញុំ ស្រឡាញ់ ភាសា ខ្មែរ
សួស្តី SokSan
ថ្ងៃនេះ ខ្ញុំ ទៅ ផ្សារ

$ echo "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ" | khmerthings segment -
ខ្ញុំ ស្រឡាញ់ ភាសា ខ្មែរ
```

Note the second line above: in the default *words mode*, punctuation (the
`!` after `SokSan`) and whitespace are dropped — the output is words only,
joined by the separator.

### `--separator SEP` — choose the joiner

Default is a single space:

```sh
$ echo "ថ្ងៃនេះខ្ញុំទៅសាលារៀន" | khmerthings segment --separator "|"
ថ្ងៃនេះ|ខ្ញុំ|ទៅ|សាលារៀន
```

Any string works, including multi-character separators (`--separator " / "`)
or a tab (`--separator "$(printf '\t')"` in a shell).

### `--mark` — insert boundaries, change nothing else

Reproduces each line exactly, only *inserting* the separator between
adjacent Khmer words. Existing spaces, punctuation, and non-Khmer text are
untouched — the "insert ZWSP" operation that line-breaking engines expect:

```sh
$ echo "ខ្ញុំទៅ ផ្សារ។ OK!" | khmerthings segment --mark --separator "|"
ខ្ញុំ|ទៅ ផ្សារ។ OK!
```

Without `--separator`, `--mark` inserts a **zero-width space** (U+200B) —
invisible in a terminal but present in the bytes:

```sh
$ echo "ខ្ញុំទៅផ្សារ" | khmerthings segment --mark        # looks unchanged...
ខ្ញុំ​ទៅ​ផ្សារ
$ echo "ខ្ញុំទៅផ្សារ" | khmerthings segment --mark | grep -c $'​'
1
```

Rule of thumb: use words mode to *extract* words, `--mark` to *annotate*
text you will keep.

### `--include modern,names,variants` — match extra wordlists

The core vocabulary is always active; `--include` adds the extra built-in
wordlists (comma-separated): `names` (personal names, surnames, honorific
titles), `modern` (slang, informal register, loanwords, trending terms),
and `variants` (common misspellings, matched as words so they can be
found and later corrected).

```sh
$ echo "សុខាដារ៉ាឡូយណាស់" | khmerthings segment
សុខាដារ៉ាឡូយ ណាស់                 # names+slang → one unknown span

$ echo "សុខាដារ៉ាឡូយណាស់" | khmerthings segment --include names,modern
សុខា ដារ៉ា ឡូយ ណាស់

$ echo "ព័ត៍មាន" | khmerthings segment --include variants
ព័ត៍មាន                            # misspelling of ព័ត៌មាន matches as a word
```

### Exit codes & errors

- `0` — success.
- `1` — an input file could not be read; a one-line message goes to stderr:
  `khmerthings: error: [Errno 2] No such file or directory: '...'`
- `2` — bad usage (unknown flag, unknown `--include` source); argparse
  prints the usage message to stderr.

## Python API

### `break_words(text, lexicon=None) -> list[str]`

Returns the words of `text` in order of appearance: Khmer words (dictionary
matches and unknown spans), Latin words, and numbers. Whitespace and
punctuation are excluded. Empty input returns `[]`.

```python
from khmerthings import break_words

break_words("ខ្ញុំ love ១២៣ 456។")
# ['ខ្ញុំ', 'love', '១២៣', '456']

break_words("")
# []
```

Unknown Khmer spans are kept as single items — never dropped, never
guessed:

```python
from khmerthings import Lexicon

lex = Lexicon(["ខ្ញុំ", "ទៅ"])            # your own dictionary
break_words("ខ្ញុំសាលារៀនទៅ", lex)
# ['ខ្ញុំ', 'សាលារៀន', 'ទៅ']              # middle item matched nothing
```

`len(break_words(text))` always equals
[`count_words(text)`](word-counter.md) — the two tools agree on what a
word is.

### `mark_boundaries(text, separator="​", lexicon=None) -> str`

Returns `text` (NFC-normalized) with `separator` inserted between adjacent
Khmer words. Nothing else changes. Default separator is the zero-width
space U+200B.

```python
from khmerthings import mark_boundaries

mark_boundaries("ខ្ញុំទៅផ្សារ")
# 'ខ្ញុំ​ទៅ​ផ្សារ'

mark_boundaries("ខ្ញុំទៅផ្សារ", separator=" | ")
# 'ខ្ញុំ | ទៅ | ផ្សារ'

mark_boundaries("ខ្ញុំទៅ ផ្សារ។ OK!", separator="|")
# 'ខ្ញុំ|ទៅ ផ្សារ។ OK!'                    # space, ។ and Latin untouched
```

Removing every `separator` from the result reproduces the NFC input exactly
(as long as the separator does not already occur in the input).

### Choosing wordlists: `load_lexicon(*sources)`

The dictionary ships as four independently growable data files, merged on
demand. `WORD_SOURCES` lists them:

| Source | Contents |
|---|---|
| `words` | core vocabulary (the default) |
| `names` | personal names, surnames, honorific titles |
| `modern` | slang, informal register, loanwords, trending vocabulary |
| `variants` | common misspellings (the keys of `load_variants()`) |

```python
from khmerthings import WORD_SOURCES, load_lexicon, load_variants, break_words

sorted(WORD_SOURCES)
# ['modern', 'names', 'variants', 'words']

lex = load_lexicon("words", "names", "modern")   # cached; any combination
break_words("ឯកឧត្តមទៅសៀមរាប", lex)
# ['ឯកឧត្តម', 'ទៅ', 'សៀមរាប']

load_lexicon("nope")
# ValueError: unknown word source 'nope'; available: ['modern', 'names', 'variants', 'words']

load_variants()["ព័ត៍មាន"]   # misspelling → canonical spelling
# 'ព័ត៌មាន'
```

Or build a fully custom dictionary: `Lexicon(iterable_of_khmer_words)` /
`Lexicon.from_lines(open("mywords.txt"))`. Entries must be NFC, Khmer
letters/marks only, and unique, or the constructor raises `ValueError`.

### Advanced: token positions

If you need character offsets or token types (e.g. to highlight words in a
UI), use the lower-level `khmerthings.tokenize(text, lexicon=None)`, which
returns `Token(text, type, start, end)` objects covering the entire input
losslessly.

## How it works

1. The text is Unicode NFC-normalized.
2. It is split into script runs (Khmer, Latin, digits, whitespace,
   punctuation). Zero-width spaces already present in the text are treated
   as explicit word delimiters, as they are in real-world Khmer text.
3. Each Khmer run is split into **character clusters** — a base consonant
   plus its subscript consonants, vowel, and signs. Clusters are the atomic
   units of Khmer script; a word boundary can only fall between clusters.
4. Words are matched **greedily, longest first**, against the hand-curated
   dictionary stored in a trie keyed by clusters.
5. Cluster runs that match no dictionary word are kept as single *unknown*
   spans — they are never dropped, and they still count as words.

## Guarantees & limitations

- **Deterministic.** Same input, same output, every time. No models, no
  randomness, no network.
- **Lossless.** No character is ever dropped or reordered; `--mark` output
  minus the separators is exactly the NFC input.
- **Accuracy scales with the dictionary.** The built-in wordlists are
  hand-curated and growing (1,895 entries across `words`/`names`/`modern`,
  plus a `variants` source of common misspellings). Words not in them come
  back as unsegmented unknown spans
  rather than being split incorrectly. Greedy longest-match can also
  occasionally over-match compounds. If segmentation quality matters for
  your use case, supply a larger `Lexicon` — or contribute words upstream
  (see [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md)).

## Task recipes

| Goal | Do this |
|---|---|
| Words of a string, as a list | `break_words(text)` |
| Best recall on real-world text | `break_words(text, load_lexicon("words", "names", "modern"))` or `--include names,modern` |
| Make Khmer text line-breakable | `mark_boundaries(text)` or `khmerthings segment --mark` |
| Visible word boundaries for review | `khmerthings segment --mark --separator "|"` |
| One word per line (for `sort`, `uniq`, …) | `khmerthings segment --separator "$(printf '\n')"` or iterate `break_words` in Python |
| Segment against a domain dictionary | `break_words(text, Lexicon.from_lines(open("domain.txt")))` |

## Related tools

- [Word counter](word-counter.md) — counts what this tool splits.
- [Line sorter](line-sorter.md) — Khmer dictionary-order sorting.
- [Spellchecker](spellcheck.md) / [Spellfixer](spellfix.md) — flag and fix
  misspellings using the same segmentation engine.
