# Condenser (`khmerthings condense`)

## What it does

Strips **function words** from Khmer text, leaving only the content
(meaning-bearing) words — a terse, "telegraphic" rendering. It is the
content-word extraction stage you run before analysis that only cares about
meaning (e.g. intent detection): particles, politeness markers, fillers,
prepositions, conjunctions, and demonstratives are removed, while the words
that actually carry meaning stay.

Each stripped word is a **stopword** tagged with a category in the curated
`stopwords.txt` data file. The categories split into two groups:

- **Removed by default** (low information): `particle`, `politeness`,
  `filler`, `preposition`, `conjunction`, `demonstrative`.
- **Kept by default** because they *carry* intent, and only removed when you
  ask: `pronoun`, `auxiliary` (modals like ចង់ "want", ត្រូវ "must",
  អាច "can"), `question` (អ្វី, ម្តេច, ប៉ុន្មាន …).

This tool is **lossy** — unlike every other khmerthings tool, its output does
not reproduce the input. Unknown Khmer spans, Latin words, and numbers are
always kept as content; punctuation and whitespace are dropped.

## Quick start

```sh
pip install khmerthings            # library
uv tool install khmerthings       # or: global CLI
```

```sh
$ echo "ខ្ញុំចង់ទៅផ្សារនៅ ព្រោះខ្ញុំចង់ទិញត្រី" | khmerthings condense
ខ្ញុំ​ចង់​ទៅ​ផ្សារ​ខ្ញុំ​ចង់​ទិញ​ត្រី
```

`នៅ` (preposition) and `ព្រោះ` (conjunction) are gone; `ខ្ញុំ` (pronoun) and
`ចង់` (the modal "want", an intent signal) are kept.

```python
from khmerthings import content_words

content_words("ខ្ញុំចង់ទៅផ្សារនៅ")
# ['ខ្ញុំ', 'ចង់', 'ទៅ', 'ផ្សារ']
```

## CLI reference

```
khmerthings condense [files ...] [--words] [--remove CAT,CAT]
                     [--include modern,names,variants]
```

Every option, with a real example of its effect:

### Input: files, multiple files, or stdin

`files` is zero or more paths; `-` or no argument reads stdin. Each input
line is condensed and printed back:

```sh
$ echo "ខ្ញុំចង់ទៅផ្សារនៅ ព្រោះខ្ញុំចង់ទិញត្រី" | khmerthings condense
ខ្ញុំ​ចង់​ទៅ​ផ្សារ​ខ្ញុំ​ចង់​ទិញ​ត្រី
```

Adjacent Khmer content words are joined by a zero-width space (U+200B, the
Khmer word delimiter — invisible in a terminal but present in the bytes),
the same convention as `segment --mark` and `normalize`:

```sh
$ echo "ខ្ញុំចង់ទៅផ្សារ" | khmerthings condense | grep -c $'​'
1
```

A normal space separates a Khmer word from an adjacent Latin word or number:

```sh
$ echo "ខ្ញុំ​ស្រឡាញ់ Facebook នៅ 2024" | khmerthings condense
ខ្ញុំ​ស្រឡាញ់ Facebook 2024
```

### `--words` — one content word per line

Emit the extracted words as a list instead of a rejoined line — the form a
downstream analyzer consumes:

```sh
$ echo "ខ្ញុំចង់ទៅផ្សារនៅ" | khmerthings condense --words
ខ្ញុំ
ចង់
ទៅ
ផ្សារ
```

### `--remove CAT,CAT` — choose which categories to strip

Overrides the default set. Add the intent-bearing categories to strip them
too — e.g. drop pronouns and auxiliaries to leave only the bare
verbs/objects:

```sh
$ echo "ខ្ញុំចង់ទៅផ្សារនៅ" | khmerthings condense --remove preposition,pronoun,auxiliary
ទៅ​ផ្សារ
```

The nine categories are: `particle`, `politeness`, `filler`, `preposition`,
`conjunction`, `demonstrative`, `pronoun`, `auxiliary`, `question`.

### `--include modern,names,variants` — match extra wordlists

The core vocabulary is always active; `--include` adds built-in wordlists so
their words segment correctly. (Stopwords are always recognized regardless of
`--include`.)

```sh
$ echo "អញ្ចឹងខ្ញុំចង់ញ៉ាំ" | khmerthings condense --include modern --words
ខ្ញុំ
ចង់
ញ៉ាំ
```

`អញ្ចឹង` (a colloquial filler) is dropped; the rest is kept.

### Exit codes & errors

- `0` — success.
- `1` — an input file could not be read; a one-line message goes to stderr:
  `khmerthings: error: [Errno 2] No such file or directory: '...'`
- `2` — bad usage (unknown flag, unknown `--include` source); argparse
  prints the usage message to stderr. An unknown `--remove` category is
  reported the same way via `parser.error`.

## Python API

### `content_words(text, lexicon=None, *, remove=None) -> list[str]`

The meaningful words of *text*, in order, with stopwords removed. `remove`
is a set of categories to strip (default: `DEFAULT_REMOVE`).

```python
from khmerthings import content_words, DEFAULT_REMOVE

content_words("ខ្ញុំចង់ទៅផ្សារនៅ")
# ['ខ្ញុំ', 'ចង់', 'ទៅ', 'ផ្សារ']

content_words("ខ្ញុំចង់ទៅផ្សារនៅ", remove=DEFAULT_REMOVE | {"pronoun", "auxiliary"})
# ['ទៅ', 'ផ្សារ']
```

### `condense_text(text, lexicon=None, *, remove=None) -> str`

The same extraction rejoined into one string (Khmer words ZWSP-joined, a
space before an adjacent Latin word or number).

```python
from khmerthings import condense_text

condense_text("ខ្ញុំចង់ទៅផ្សារនៅ")
# 'ខ្ញុំ​ចង់​ទៅ​ផ្សារ'
```

### `content_tokens(text, lexicon=None, *, remove=None) -> list[Token]`

The kept tokens as typed [`Token`](word-breaker.md) objects, with `type`,
`start`, and `end` offsets into the NFC-normalized input — use this when you
need positions or token types, not just the strings.

### `load_stopwords() -> dict[str, str]`

The built-in stopword → category map, as loaded from `stopwords.txt`. The
category constant `STOPWORD_CATEGORIES` and the default-removed set
`DEFAULT_REMOVE` are also importable from `khmerthings`.

```python
from khmerthings import load_stopwords

load_stopwords()["ទេ"]
# 'particle'
```

## How it works

1. The text is tokenized exactly like the [word breaker](word-breaker.md) —
   greedy longest match over character clusters — against the chosen lexicon
   *plus every stopword*, so stopwords always surface as single tokens even
   with a minimal caller lexicon.
2. Non-word tokens (punctuation, whitespace) are dropped. Each remaining
   Khmer word is looked up in the stopword map; if its category is in the
   active `remove` set, it is dropped too. Everything else — content Khmer
   words, unknown Khmer spans, Latin words, numbers — is kept.
3. `condense_text` rejoins the kept tokens: a zero-width space between two
   adjacent Khmer words, a single space when a Latin word or number sits
   next to a Khmer word.

## Guarantees & limitations

- **Deterministic.** Same input, same output, every time. No models, no
  randomness, no network.
- **Lossy by design.** The output is a reduction; it does not reproduce the
  input. (This is the one khmerthings tool that is not information-preserving.)
- **A stopword inside a lexicon compound is not split.** `ថ្ងៃនេះ` ("today")
  is a single dictionary word, so the `នេះ` inside it is never a separate
  token and the whole word survives as content — correct, since it means
  "today", not "day" + "this".
- **Conservative stoplist.** Verb/preposition-ambiguous words (`ទៅ` go/to,
  `មក` come/toward, `ណា` which/softener) are deliberately left out rather
  than risk stripping content. The list is curated and growable.
- **Accuracy scales with the dictionary**, same as the
  [word breaker](word-breaker.md) — unrecognized spans are kept intact as a
  single content unit, never guessed at, and are never treated as stopwords.

## Task recipes

| Goal | Do this |
|---|---|
| Reduce text to content words (terse form) | `khmerthings condense in.txt` |
| Get the meaningful-word list for analysis | `khmerthings condense --words in.txt` |
| Also drop pronouns/modals, keep bare verbs & objects | `khmerthings condense --remove particle,politeness,filler,preposition,conjunction,demonstrative,pronoun,auxiliary in.txt` |
| Strip only sentence-final particles | `khmerthings condense --remove particle in.txt` |
| Condense a string in Python | `condense_text(text)` |
| Feed content words to your own analyzer | `content_words(text)` |
| Condense informal/social-media text | `khmerthings condense --include names,modern file.txt` |

## Related tools

- [Word breaker](word-breaker.md) — the segmentation engine underneath, and
  the source of the ZWSP boundary convention.
- [Normalizer](normalize.md) — clean text up *losslessly* first, then
  condense.
- [Word counter](word-counter.md) — count words without removing any.
