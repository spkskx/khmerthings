# Orthography validator (`khmerthings validate`)

## What it does

Reports definite structural errors in Khmer Unicode text without rewriting it. It checks
orphan marks and coeng, invalid coeng followers, repeated dependent vowels or register
shifters, and invalid ordering of register shifters, vowels, and trailing signs.

## Quick start

```sh
$ printf 'ក្ឥ\n' | khmerthings validate
<stdin>:1:2: invalid_coeng_follower: ្ឥ
```

```python
from khmerthings import validate_orthography

validate_orthography("ក")   # ()
validate_orthography("កាិ")[0].code.value   # 'repeated_dependent_vowel'
```

## CLI reference

```
khmerthings validate [files ...] [--json]
```

### Input files or stdin

Zero paths reads stdin. `-` also means stdin. Multiple files are checked in order.

```sh
$ printf 'ក\n' | khmerthings validate
```

Clean input prints nothing and exits 0.

### `--json`

```sh
$ printf 'កាិ\n' | khmerthings validate --json
[
  {
    "source": "<stdin>",
    "line": 1,
    "col": 3,
    "start": 2,
    "end": 3,
    "text": "ិ",
    "code": "repeated_dependent_vowel"
  }
]
```

### Exit codes and errors

- `0` — no issues.
- `1` — one or more issues, or unreadable input file.
- `2` — bad CLI usage; argparse writes usage and error text to stderr.

Missing file example:

```text
khmerthings: error: [Errno 2] No such file or directory: 'missing.txt'
```

## Python API

### `validate_orthography(text) -> tuple[OrthographyIssue, ...]`

Input is NFC-normalized. Results are ordered by `(start, end, code)`; offsets reference
normalized text.

```python
from khmerthings import OrthographyIssueCode, validate_orthography

issue = validate_orthography("ក្ឥ")[0]
issue.text                         # '្ឥ'
issue.start, issue.end             # (1, 3)
issue.code is OrthographyIssueCode.INVALID_COENG_FOLLOWER  # True
```

`OrthographyIssue` is frozen and contains `text`, `start`, `end`, and `code`.
`OrthographyIssueCode` values are stable machine-readable strings.

## How it works

A stdlib-only deterministic scanner tracks whether it is inside a Khmer orthographic
syllable and whether a register shifter, dependent vowel, or trailing sign has appeared.
It validates coeng followers directly against Khmer consonant code points. It ignores
non-Khmer text and never consults a dictionary.

## Guarantees and limitations

- Deterministic: no model, randomness, network, or corpus scoring.
- Read-only: never fixes, drops, or reorders characters.
- Conservative: reports definite Unicode structure errors, not vocabulary errors.
- NFC offsets: indices refer to normalized input, not necessarily original decomposed input.
- It does not decide whether a correctly encoded sequence is a real Khmer word.
- It does not restrict stacked consonant count; valid Sanskrit/Pali-derived structures must
  not be rejected by a speculative maximum.

## Task recipes

| Goal | Command or call |
|---|---|
| Validate stdin | `khmerthings validate` |
| Validate files | `khmerthings validate a.txt b.txt` |
| Produce JSON | `khmerthings validate --json text.txt` |
| Check in Python | `validate_orthography(text)` |
| Test one issue code | `issue.code is OrthographyIssueCode.ORPHAN_MARK` |

## Related tools

- [Normalizer](normalize.md) — fixes curated spelling variants and spacing; it does not
  silently repair orthographic structure.
- [Spellchecker](spellcheck.md) — checks known variants and unknown words.
- [Word breaker](word-breaker.md) — segments text losslessly, including malformed text.
