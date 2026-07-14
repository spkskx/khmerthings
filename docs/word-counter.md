# Word counter (`khmerthings count`)

## What it does

Counts words and characters in Khmer or mixed Khmer/Latin text. In English,
counting words means splitting on spaces; Khmer script writes **no spaces
between words**, so a Khmer word counter must first find the word boundaries
with a dictionary. This tool does that, and reports a full breakdown: Khmer
words, unknown Khmer spans, Latin words, numbers, character clusters, and
raw character counts.

Typical uses: word-count limits for articles and translations, corpus
statistics, pricing translation work, progress metrics for writing tools.

## Quick start

```sh
pip install khmerthings            # library
uv tool install khmerthings       # or: global CLI
```

```sh
$ echo "ខ្ញុំមានឆ្កែ ២ ក្បាល and 3 cats" | khmerthings count
  total_words: 8
  khmer_words: 4
  unknown_khmer_words: 0
  latin_words: 2
  numbers: 2
  clusters: 7
  khmer_characters: 18
  characters: 32
```

```python
from khmerthings import count_words

count_words("ខ្ញុំមានឆ្កែ ២ ក្បាល and 3 cats")
# 8
```

## What counts as a word

`total_words` is the sum of:

| Category | Example | Counted as |
|---|---|---|
| Khmer word found in the dictionary | ខ្ញុំ | 1 each |
| Contiguous Khmer span *not* in the dictionary | a rare name | 1 per span |
| Latin-script word | `hello` | 1 each |
| Number (Arabic `123` or Khmer `១២៣` digits) | ២ | 1 each |

Whitespace (including zero-width spaces) and punctuation are not words.
This definition is shared with the [word breaker](word-breaker.md):
`count_words(text) == len(break_words(text))` always holds.

## CLI reference

```
khmerthings count [files ...] [--json] [--include modern,names,variants]
```

Every option, with a real example of its effect:

### Input: files, multiple files, or stdin

`files` is zero or more paths; `-` or no argument reads stdin. With
multiple files, each result block is labelled with its path:

```sh
$ khmerthings count a.txt b.txt
a.txt:
  total_words: 6
  khmer_words: 5
  unknown_khmer_words: 0
  latin_words: 1
  numbers: 0
  clusters: 10
  khmer_characters: 27
  characters: 37
b.txt:
  total_words: 4
  khmer_words: 4
  unknown_khmer_words: 0
  latin_words: 0
  numbers: 0
  clusters: 6
  khmer_characters: 19
  characters: 20
```

### `--json` — machine-readable output

Always a JSON array (even for one input), one object per input, fields in a
fixed order. `source` is the file path, or `<stdin>`:

```sh
$ echo "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ" | khmerthings count --json
[
  {
    "source": "<stdin>",
    "total_words": 4,
    "khmer_words": 4,
    "unknown_khmer_words": 0,
    "latin_words": 0,
    "numbers": 0,
    "clusters": 8,
    "khmer_characters": 21,
    "characters": 22
  }
]
```

(`characters` is 22 here because `echo` appends a newline.) Parse with
`jq`: `khmerthings count --json *.txt | jq 'map(.total_words) | add'`.

### `--include modern,names,variants` — match extra wordlists

The core vocabulary is always active; `--include` adds the `names`
(personal names, surnames, titles), `modern` (slang, loanwords), and/or
`variants` (common misspellings) wordlists, so such text counts as known
words instead of unknown spans:

```sh
$ echo "ហ្វេសប៊ុកឡូយណាស់" | khmerthings count | grep -E "khmer_words|unknown"
  khmer_words: 3
  unknown_khmer_words: 3

$ echo "ហ្វេសប៊ុកឡូយណាស់" | khmerthings count --include modern | grep -E "khmer_words|unknown"
  khmer_words: 3
  unknown_khmer_words: 0
```

(Without `modern`, the counter even mis-finds the core words ស and ក inside
the loanword ហ្វេសប៊ុក — a concrete example of why the right wordlist
matters.)

### Exit codes & errors

- `0` — success.
- `1` — an input file could not be read; one-line message on stderr:
  `khmerthings: error: [Errno 2] No such file or directory: '...'`
- `2` — bad usage (unknown flag, unknown `--include` source).

## Python API

### `count_words(text, lexicon=None) -> int`

The total word count, as defined above. Empty or whitespace-only text
returns `0`.

```python
from khmerthings import count_words

count_words("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ")   # 4
count_words("hello beautiful world")     # 3
count_words("។៕ !?")                     # 0 (punctuation only)
count_words("")                          # 0
```

### `analyze(text, lexicon=None) -> WordCount`

The full breakdown as an immutable (frozen) dataclass:

```python
from khmerthings import analyze

analyze("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ")
# WordCount(total_words=4, khmer_words=4, unknown_khmer_words=0,
#           latin_words=0, numbers=0, clusters=8, khmer_characters=21,
#           characters=21)
```

Field meanings:

- `total_words` — sum of the four word categories below.
- `khmer_words` / `unknown_khmer_words` — dictionary-matched words vs
  unknown Khmer spans. A high unknown count means the dictionary is missing
  vocabulary for your text, not that the text is wrong.
- `latin_words` — runs of non-Khmer letters.
- `numbers` — number tokens, whether Arabic (`456`) or Khmer (`១២៣`) digits.
- `clusters` — Khmer character clusters (user-perceived characters), often
  more useful than codepoint counts for Khmer.
- `khmer_characters` / `characters` — codepoint counts (Khmer only, and the
  whole NFC-normalized text respectively).

It serializes cleanly for pipelines:

```python
import dataclasses, json

json.dumps(dataclasses.asdict(analyze("ខ្ញុំ love ១២៣")), ensure_ascii=False)
# {"total_words": 3, "khmer_words": 1, "unknown_khmer_words": 0,
#  "latin_words": 1, "numbers": 1, "clusters": 4, "khmer_characters": 8,
#  "characters": 14}
```

### Counting with other wordlists

Pass any `Lexicon` via `lexicon=` — a merged built-in one or your own:

```python
from khmerthings import Lexicon, analyze, load_lexicon

analyze("សុខាឡូយ").unknown_khmer_words                                    # 1
analyze("សុខាឡូយ", load_lexicon("words", "names", "modern")).unknown_khmer_words  # 0

analyze(text, lexicon=Lexicon.from_lines(open("domain.txt")))   # custom
```

See the [word breaker doc](word-breaker.md#choosing-wordlists-load_lexiconsources)
for the list of built-in wordlist sources.

## How it works

The text is NFC-normalized and run through the same deterministic pipeline
as the [word breaker](word-breaker.md): script-run splitting → character
cluster segmentation → greedy longest-match against the hand-curated
dictionary. The counter then tallies the resulting tokens by type.

## Guarantees & limitations

- **Deterministic.** Same input, same output, every time.
- **Nothing is silently dropped.** Khmer text missing from the dictionary is
  still counted (as unknown spans), so totals never undercount to zero on
  rare vocabulary — but note that one unknown *span* may actually contain
  several real words, so Khmer word counts on dictionary-poor text are a
  lower bound. The `unknown_khmer_words` field tells you how much of the
  text that caveat applies to.
- **Accuracy scales with the dictionary** (1,895 hand-curated entries across
  the `words`/`names`/`modern` sources and growing, plus a `variants`
  source of common misspellings). Use
  `--include`/`load_lexicon`, supply your own `Lexicon`, or contribute
  words upstream (see [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md)).

## Task recipes

| Goal | Do this |
|---|---|
| Just the number | `count_words(text)` |
| Full stats, programmatic | `analyze(text)` (frozen dataclass) |
| Full stats, shell pipeline | `khmerthings count --json ... \| jq` |
| Best accuracy on names/slang-heavy text | add `--include names,modern` / `load_lexicon("words", "names", "modern")` |
| Judge dictionary coverage of a corpus | compare `unknown_khmer_words` vs `khmer_words` |
| Word count of many files, total | `khmerthings count --json *.txt \| jq 'map(.total_words) | add'` |

## Related tools

- [Word breaker](word-breaker.md) — returns the words this tool counts.
- [Line sorter](line-sorter.md) — Khmer dictionary-order sorting.
  `unknown_khmer_words`.
