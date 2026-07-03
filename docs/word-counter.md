# Word counter (`khmerthings count`)

## What it does

Counts words and characters in Khmer or mixed Khmer/Latin text. In English,
counting words means splitting on spaces; Khmer script writes **no spaces
between words**, so a Khmer word counter must first find the word boundaries
with a dictionary. This tool does that, and reports a full breakdown: Khmer
words, unknown Khmer spans, Latin words, numbers, character clusters, and
raw character counts.

Typical uses: word-count limits for articles and translations, corpus
statistics, pricing translation work, and progress metrics for writing
tools.

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
khmerthings count [files ...] [--json]
```

- **`files`** — one or more input files; `-` or no argument reads stdin.
  With multiple files, each result is labelled with its filename.
- **`--json`** — machine-readable output: a JSON array with one object per
  input, each carrying a `source` field plus all count fields.
- **`--include names,modern`** — also match against the extra built-in
  wordlists (`names`: personal names and titles; `modern`: slang and
  loanwords), so e.g. names count as known words instead of unknown spans.
- Exit code 0 on success.

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

(`characters` is 22 here because `echo` appends a newline.)

## Python API

### `count_words(text, lexicon=None) -> int`

The total word count, as defined above.

### `analyze(text, lexicon=None) -> WordCount`

The full breakdown as an immutable dataclass:

```python
from khmerthings import analyze

analyze("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ")
# WordCount(total_words=4, khmer_words=4, unknown_khmer_words=0,
#           latin_words=0, numbers=0, clusters=8, khmer_characters=21,
#           characters=21)
```

Field meanings:

- `khmer_words` / `unknown_khmer_words` — dictionary-matched words vs
  unknown Khmer spans (a high unknown count means the dictionary is missing
  vocabulary for your text, not that the text is wrong).
- `numbers` — number tokens, whether Arabic (`456`) or Khmer (`១២៣`) digits.
- `clusters` — Khmer character clusters (user-perceived characters), often
  more useful than codepoint counts for Khmer.
- `khmer_characters` / `characters` — codepoint counts (of Khmer characters,
  and of the whole NFC-normalized text).

Both functions accept `lexicon=` (a `khmerthings.Lexicon`) to count against
your own wordlist, or a merged built-in one:

```python
from khmerthings import analyze, load_lexicon

analyze(text, lexicon=load_lexicon("words", "names", "modern"))
```

See the [word breaker doc](word-breaker.md) for the list of built-in
wordlist sources.

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
- **Accuracy scales with the dictionary** (802 hand-curated entries across
  the `words`/`names`/`modern` sources as of v0.4.0, growing). Supply your
  own `Lexicon`, use `--include`, or contribute words upstream (see
  [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md)).

## Related tools

- [Word breaker](word-breaker.md) — returns the words this tool counts.
- [Line sorter](line-sorter.md) — Khmer dictionary-order sorting.
