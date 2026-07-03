# Word breaker (`khmerthings segment`)

## What it does

Splits Khmer text into words. Khmer script writes **no spaces between
words** — spaces only separate phrases — so "splitting on whitespace" does
not work for Khmer the way it does for English. The word breaker finds the
word boundaries using a dictionary and a deterministic longest-match
algorithm, and gives you the result either as a list of words or as the
original text with boundary markers inserted.

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
khmerthings segment [files ...] [--separator SEP] [--mark]
```

- **`files`** — one or more input files; `-` or no argument reads stdin.
  Each line of input produces one line of output.
- **`--separator SEP`** — the string placed between words. Defaults to a
  single space, or to a zero-width space (U+200B) in `--mark` mode.
- **`--mark`** — instead of listing words, reproduce each line exactly as-is
  and only *insert* the separator at Khmer word boundaries. Existing spaces
  and punctuation are untouched. This is the "insert ZWSP" operation that
  line-breaking engines and many text pipelines expect.
- **`--include names,modern`** — also match against the extra built-in
  wordlists: `names` (personal names, surnames, honorific titles) and
  `modern` (slang, informal register, loanwords, trending vocabulary).
  The core wordlist is always active.
- Exit code 0 on success.

Examples (real output):

```sh
$ echo "ថ្ងៃនេះខ្ញុំទៅសាលារៀន" | khmerthings segment --separator "|"
ថ្ងៃនេះ|ខ្ញុំ|ទៅ|សាលារៀន

$ echo "ខ្ញុំទៅ ផ្សារ។" | khmerthings segment --mark --separator "·"
ខ្ញុំ·ទៅ ផ្សារ។
```

Note how `--mark` kept the existing space and the ។ untouched and only
inserted a marker between the two adjacent Khmer words.

Names and slang segment correctly once their wordlists are included:

```sh
$ echo "សុខាដារ៉ាទៅភ្នំពេញ" | khmerthings segment --include names
សុខា ដារ៉ា ទៅ ភ្នំពេញ

$ echo "ហ្វេសប៊ុកឡូយណាស់" | khmerthings segment --include modern
ហ្វេសប៊ុក ឡូយ ណាស់
```

## Python API

### `break_words(text, lexicon=None) -> list[str]`

Returns the words of `text` in order of appearance: Khmer words (dictionary
matches and unknown spans), Latin words, and numbers. Whitespace and
punctuation are excluded.

```python
from khmerthings import break_words

break_words("ខ្ញុំ love ១២៣ 456។")
# ['ខ្ញុំ', 'love', '១២៣', '456']
```

`len(break_words(text))` always equals
[`count_words(text)`](word-counter.md) — the two tools agree on what a word
is.

### `mark_boundaries(text, separator="​", lexicon=None) -> str`

Returns `text` (NFC-normalized) with `separator` inserted between adjacent
Khmer words. Nothing else changes.

```python
from khmerthings import mark_boundaries

mark_boundaries("ខ្ញុំទៅផ្សារ")
# 'ខ្ញុំ​ទៅ​ផ្សារ'

mark_boundaries("ខ្ញុំទៅផ្សារ", separator=" | ")
# 'ខ្ញុំ | ទៅ | ផ្សារ'
```

Removing every `separator` from the result reproduces the NFC input exactly
(as long as the separator does not already occur in the input).

### Choosing wordlists: `load_lexicon(*sources)`

The dictionary ships as three independently growable data files, merged on
demand:

| Source | Contents |
|---|---|
| `words` | core vocabulary (the default) |
| `names` | personal names, surnames, honorific titles |
| `modern` | slang, informal register, loanwords, trending vocabulary |

```python
from khmerthings import load_lexicon, break_words

lex = load_lexicon("words", "names", "modern")
break_words("ឯកឧត្តមទៅសៀមរាប", lex)
# ['ឯកឧត្តម', 'ទៅ', 'សៀមរាប']
```

Both functions also accept any custom `khmerthings.Lexicon` you build from
your own wordlist.

## How it works

1. The text is Unicode NFC-normalized.
2. It is split into script runs (Khmer, Latin, digits, whitespace,
   punctuation). Zero-width spaces already present in the text are treated
   as explicit word delimiters, as they are in real-world Khmer text.
3. Each Khmer run is split into **character clusters** — a base consonant
   plus its subscript consonants, vowel, and signs. Clusters are the atomic
   units of Khmer script; a word boundary can only fall between clusters.
4. Words are matched **greedily, longest first**, against a hand-curated
   dictionary stored in a trie keyed by clusters.
5. Cluster runs that match no dictionary word are kept as single *unknown*
   spans — they are never dropped, and they still count as words.

## Guarantees & limitations

- **Deterministic.** Same input, same output, every time. No models, no
  randomness, no network.
- **Lossless.** No character is ever dropped or reordered; `--mark` output
  minus the separators is exactly the NFC input.
- **Accuracy scales with the dictionary.** The built-in wordlists are
  hand-curated and growing (802 entries across `words`/`names`/`modern` as
  of v0.4.0). Words not in them come back as unsegmented unknown spans
  rather than being split incorrectly.
  Greedy longest-match can also occasionally over-match compounds. If
  segmentation quality matters for your use case, you can supply your own
  larger `Lexicon` — or contribute words upstream (see
  [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md)).

## Related tools

- [Word counter](word-counter.md) — counts what this tool splits.
- [Line sorter](line-sorter.md) — Khmer dictionary-order sorting.
