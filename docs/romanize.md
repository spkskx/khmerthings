# Romanizer (`khmerthings romanize`)

## What it does

Turns Khmer script into a readable Latin approximation of how it sounds —
e.g. ភ្នំពេញ → `phnom penh` — following the two-register (a-series /
o-series) system that governs Khmer vowel pronunciation. It is a
deterministic rule engine backed by a hand-curated **exception lexicon**
(`romanize.txt`) that overrides the rules for irregular words and
established place-name spellings.

It is **phonetic, not reversible**: different Khmer spellings can romanize
the same way, and the Latin output cannot be mapped back to a unique Khmer
spelling. If you need a lossless round-trip, this is not that tool.

## Quick start

```sh
pip install khmerthings            # library
uv tool install khmerthings       # or: global CLI
```

```sh
$ echo "ភ្នំពេញ" | khmerthings romanize
phnom penh
```

```python
from khmerthings import romanize

romanize("ភ្នំពេញ")
# 'phnom penh'
```

## CLI reference

```
khmerthings romanize [files ...] [--include modern,names,variants]
```

Every option, with a real example of its effect:

### Input: files, multiple files, or stdin

`files` is zero or more paths; `-` or no argument reads stdin. Each input
line is romanized and printed back, files processed in order. Adjacent
Khmer words (which Khmer writes with no space between them) are separated by
a space in the output; non-Khmer text passes through unchanged:

```sh
$ printf 'ភ្នំពេញ\nសៀមរាប\n' | khmerthings romanize
phnom penh
siem reap
```

```sh
$ echo "ខ្ញុំទៅសាលា" | khmerthings romanize
khnhum tau salea
```

Khmer digits are rendered as Arabic numerals:

```sh
$ echo "តម្លៃ ២៥០០ រៀល" | khmerthings romanize
tamley 2500 riel
```

### `--include modern,names,variants` — romanize extra wordlists as words

The core vocabulary is always active; `--include` adds the extra built-in
wordlists (comma-separated) to what tokenizes as a single word before
romanization. Use it when your text contains names or slang so they are
segmented (and looked up in the exception lexicon) as whole words:

```sh
$ echo "ភ្នំពេញ" | khmerthings romanize --include names
phnom penh
```

### Exit codes & errors

- `0` — success.
- `1` — an input file could not be read; a one-line message goes to stderr:
  `khmerthings: error: [Errno 2] No such file or directory: '...'`
- `2` — bad usage (unknown flag, unknown `--include` source); argparse
  prints the usage message to stderr.

## Python API

### `romanize(text, lexicon=None) -> str`

Returns a phonetic Latin romanization of `text` (NFC-normalized). Khmer
words are looked up in the exception lexicon first and otherwise romanized
by rule; Khmer digits become Arabic numerals; non-Khmer text is copied
verbatim.

```python
from khmerthings import romanize

romanize("ភ្នំពេញ")   # exception-lexicon spelling
# 'phnom penh'

romanize("ខ្មែរ")
# 'khmer'
```

`lexicon` defaults to the core `words` source and, unioned with the
exception-lexicon keys, controls how the text is split into words:

```python
from khmerthings import load_lexicon

romanize("ភ្នំពេញ", load_lexicon("words", "names"))
# 'phnom penh'
```

### The exception table: `load_romanizations()`

The exception lexicon is a plain `dict[str, str]` you can inspect:

```python
from khmerthings import load_romanizations

load_romanizations()["ភ្នំពេញ"]
# 'phnom penh'
```

## How it works

1. The text is NFC-normalized and tokenized exactly like the
   [word breaker](word-breaker.md) does — greedy longest match over
   character clusters — against the chosen lexicon *plus* the exception-lexicon
   keys, so every exception entry surfaces as a single word.
2. Each Khmer word is romanized: if the whole word is an exception-lexicon
   entry, its curated spelling wins; otherwise the word is processed cluster
   by cluster. Each cluster resolves a consonant series (1st/2nd register —
   flipped by the register shifters muusikatoan ៉ and triisap ៊), an onset
   (base consonant plus any subscript consonants), and a vowel. Dependent
   vowels read differently per register; a bare consonant takes the
   register's inherent vowel unless it closes a syllable, where it reads as
   a final consonant (e.g. the ញ in ពេញ → `penh`).
3. Khmer digits become Arabic numerals; non-Khmer runs pass through.

## Guarantees & limitations

- **Deterministic.** Same input, same output, every time. No models, no
  randomness, no network.
- **Phonetic, not reversible.** The output approximates pronunciation; it
  cannot be transformed back into a unique Khmer spelling.
- **An approximation.** The rule engine is a practical approximation of
  UNGEGN 1972 order, not a full phonological model — it does not resolve
  every context-dependent vowel or final-consonant subtlety. The exception
  lexicon exists precisely to correct words the rules get wrong; it grows
  with no code changes.
- **Non-Khmer is preserved.** Latin, numbers, and punctuation are copied
  through unchanged; Khmer digits are converted to Arabic.

## Task recipes

| Goal | Do this |
|---|---|
| Romanize a file | `khmerthings romanize in.txt > out.txt` |
| Romanize a string in Python | `romanize(text)` |
| Romanize names/slang correctly segmented | `khmerthings romanize --include names,modern f.txt` |
| Add a custom spelling | append `khmer<TAB>latin` to `romanize.txt` (source install) |
| Inspect all exception spellings | `python -c "from khmerthings import load_romanizations; [print(k, '->', v) for k, v in load_romanizations().items()]"` |

## Related tools

- [Word breaker](word-breaker.md) — the segmentation engine underneath.
- [Numerals](numerals.md) — convert Khmer/Arabic digits and spell numbers.
- [Normalizer](normalize.md) — clean and re-space Khmer before romanizing.
