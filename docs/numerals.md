# Numerals (`khmerthings numerals`)

## What it does

Converts numbers between three forms:

- **Khmer digits** ០១២៣៤៥៦៧៨៩ ⇄ **Arabic digits** 0123456789 (a 1:1,
  reversible digit transliteration), and
- **spelled-out Khmer words** — e.g. `123` → មួយរយម្ភៃបី — using the
  traditional decimal-unit number system (ដប់, រយ, ពាន់, ម៉ឺន, សែន, លាន).

Digit conversion touches only digit characters; everything else passes
through unchanged, so Khmer↔Arabic round-trips exactly on the digit subset.

## Quick start

```sh
pip install khmerthings            # library
uv tool install khmerthings       # or: global CLI
```

```sh
$ echo "2026" | khmerthings numerals
២០២៦
```

```python
from khmerthings import arabic_to_khmer, khmer_to_arabic, number_to_words

arabic_to_khmer("2026")   # '២០២៦'
khmer_to_arabic("២០២៦")   # '2026'
number_to_words(2500)      # 'ពីរពាន់ប្រាំរយ'
```

## CLI reference

```
khmerthings numerals [files ...] [--to {khmer,arabic,words}]
```

Every option, with a real example of its effect:

### Input: files, multiple files, or stdin

`files` is zero or more paths; `-` or no argument reads stdin. Each input
line is converted and printed back, files processed in order.

### `--to khmer` (default) — Arabic digits → Khmer digits

```sh
$ echo "2026" | khmerthings numerals --to khmer
២០២៦
```

### `--to arabic` — Khmer digits → Arabic digits

Non-digit characters are left untouched:

```sh
$ echo "ឆ្នាំ ២០២៦" | khmerthings numerals --to arabic
ឆ្នាំ 2026
```

### `--to words` — spell every number in Khmer words

Each run of digits (Arabic or Khmer) is replaced by its spelled-out Khmer
form; surrounding text is preserved:

```sh
$ echo "តម្លៃ 2500 រៀល" | khmerthings numerals --to words
តម្លៃ ពីរពាន់ប្រាំរយ រៀល
```

### Exit codes & errors

- `0` — success.
- `1` — an input file could not be read; a one-line message goes to stderr:
  `khmerthings: error: [Errno 2] No such file or directory: '...'`
- `2` — bad usage (unknown flag, unknown `--to` value); argparse prints the
  usage message to stderr.

## Python API

### `arabic_to_khmer(text) -> str` / `khmer_to_arabic(text) -> str`

Transliterate the ten digit characters in either direction. Only digits
change; the two functions are inverses on the digit subset.

```python
from khmerthings import arabic_to_khmer, khmer_to_arabic

arabic_to_khmer("A320")   # 'A៣២០'
khmer_to_arabic("A៣២០")   # 'A320'
```

### `number_to_words(n) -> str`

Spell the integer `n` in Khmer. Zero is សូន្យ; negative numbers are
prefixed with ដក; the decimal units compose left to right, recursing
through លាន above one million.

```python
from khmerthings import number_to_words

number_to_words(0)      # 'សូន្យ'
number_to_words(2500)   # 'ពីរពាន់ប្រាំរយ'
number_to_words(-5)     # 'ដកប្រាំ'
```

## How it works

- **Digit conversion** is a pure character-translation table over the two
  0–9 ranges (Arabic `0`–`9`, Khmer ០–៩ = U+17E0–U+17E9). Every other
  character is passed through, so the transform is reversible on digits.
- **Spelling** recurses over the decimal units — ones, ដប់ (10), ម្ភៃ (20)
  and the ...សិប tens, then រយ/ពាន់/ម៉ឺន/សែន/លាន. Numbers at or above one
  million are expressed as a multiplier of លាន (e.g. 10⁷ → ដប់លាន). The unit
  words are fixed grammar, held in-module (no data file).

## Guarantees & limitations

- **Deterministic.** Same input, same output, every time. No models, no
  randomness, no network.
- **Digit conversion is reversible and lossless.** Only digits change;
  `khmer_to_arabic(arabic_to_khmer(s)) == s` for any string of digits.
- **Spelling covers integers only.** `number_to_words` takes an `int`
  (including zero and negatives); it does not spell decimals, fractions, or
  ordinals.
- **CLI `--to words` spells whole digit runs.** A run like `2500` becomes
  one number; it does not interpret grouping separators (`2,500`) — strip or
  normalize those first.

## Task recipes

| Goal | Do this |
|---|---|
| Convert a file's numbers to Khmer digits | `khmerthings numerals in.txt > out.txt` |
| Convert Khmer digits to Arabic | `khmerthings numerals --to arabic in.txt` |
| Spell numbers out in Khmer | `khmerthings numerals --to words in.txt` |
| Convert digits in Python | `arabic_to_khmer(text)` / `khmer_to_arabic(text)` |
| Spell one integer | `number_to_words(2500)` |

## Related tools

- [Word counter](word-counter.md) — reports how many numbers a text contains.
- [Romanizer](romanize.md) — renders Khmer digits as Arabic while romanizing.
- [Normalizer](normalize.md) — clean and re-space Khmer text.
