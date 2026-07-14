# Normalizer (`khmerthings normalize`)

## What it does

Turns loosely-typed, raw Khmer text into clean, ready-to-use text in one
pass. It composes three independently-callable, deterministic steps:

1. **Spellfix** (`fix_spelling`, internal spelling correction pass) — known
   misspellings from the hand-curated variants map are rewritten to their
   canonical spelling.
2. **Hidden-space placement** (`space_words`) — a zero-width space (U+200B)
   is inserted between adjacent Khmer/Latin/number words that have no
   separator at all (the same boundary rule
   [`mark_boundaries`](word-breaker.md) uses). Whitespace elsewhere is
   collapsed to a single space and leading/trailing whitespace is dropped.
   A visible space a human already placed between two words (a phrase
   break) is never downgraded to invisible — it stays a single visible
   space.
3. **Sentence-stop spacing** (`space_sentences`) — whitespace immediately
   before a Khmer full stop (។ khan, ៕ bariyoosan) is dropped, and exactly
   one space is ensured immediately after it. This step is a pure string
   scan — no tokenizer, no lexicon.

Each step is also usable on its own — see the Python API section — but
`normalize`/`normalize_text` remain the one CLI subcommand and function;
the individual passes are exposed as library-level refinements and a
`--only` flag, not separate tools.

## Quick start

```sh
pip install khmerthings            # library
uv tool install khmerthings       # or: global CLI
```

```sh
$ echo "ខ្ញុំសំរាប់ការងារ" | khmerthings normalize
ខ្ញុំ​សម្រាប់​ការងារ
```

```python
from khmerthings import normalize_text

normalize_text("ខ្ញុំសំរាប់ការងារ")
# 'ខ្ញុំ​សម្រាប់​ការងារ'
```

## CLI reference

```
khmerthings normalize [files ...] [--only {words,sentences}] [--include modern,names,variants]
```

Every option, with a real example of its effect:

### Input: files, multiple files, or stdin

`files` is zero or more paths; `-` or no argument reads stdin. Every input
line is printed back normalized, files processed in order:

```sh
$ printf 'សំរាប់ កំរិត\nខ្ញុំទៅផ្សារ\n' | khmerthings normalize
សម្រាប់ កម្រិត
ខ្ញុំ​ទៅ​ផ្សារ
```

### Word boundaries get a hidden space

```sh
$ echo "ខ្ញុំទៅផ្សារ" | khmerthings normalize
ខ្ញុំ​ទៅ​ផ្សារ
```

Invisible in a terminal but present in the bytes — same convention as
`segment --mark`:

```sh
$ echo "ខ្ញុំទៅផ្សារ" | khmerthings normalize | grep -c $'​'
1
```

### Whitespace is collapsed and trimmed

```sh
$ echo "ខ្ញុំទៅ  ផ្សារ" | khmerthings normalize
ខ្ញុំ​ទៅ ផ្សារ
```

The double space between the words becomes a single visible space (a
human-placed phrase break, preserved — not turned into a hidden space), and
leading/trailing whitespace on the line disappears entirely.

### Sentence stops get tidied

```sh
$ echo "ខ្ញុំទៅផ្សារ ។ទិញត្រី" | khmerthings normalize
ខ្ញុំ​ទៅ​ផ្សារ។ ទិញ​ត្រី
```

The space before ។ is dropped, and one is inserted after it even though the
input had none.

### `--only {words,sentences}` — apply a single pass

`words` runs spellfix + hidden-space placement + whitespace collapse, but
skips sentence-stop spacing; `sentences` runs only the sentence-stop pass.
`sentences` ignores `--include` and the lexicon entirely — `space_sentences`
takes no lexicon argument at all, so this is not a bug:

```sh
$ echo "ខ្ញុំទៅផ្សារ ។ទិញត្រី" | khmerthings normalize --only words
ខ្ញុំ​ទៅ​ផ្សារ ។ទិញ​ត្រី
$ echo "ខ្ញុំទៅផ្សារ ។ទិញត្រី" | khmerthings normalize --only sentences
ខ្ញុំទៅផ្សារ។ ទិញត្រី
```

### `--include modern,names,variants` — match extra wordlists

The core vocabulary is always active; `--include` adds the extra built-in
wordlists (comma-separated) so their words segment correctly (and their
own spellings are never treated as misspellings):

```sh
$ echo "សុខាដារ៉ាឡូយណាស់" | khmerthings normalize --include names,modern
សុខា​ដារ៉ា​ឡូយ​ណាស់
```

### Exit codes & errors

- `0` — success (whether or not anything was rewritten).
- `1` — an input file could not be read; a one-line message goes to stderr:
  `khmerthings: error: [Errno 2] No such file or directory: '...'`
- `2` — bad usage (unknown flag, unknown `--include` source); argparse
  prints the usage message to stderr.

## Python API

### `space_words(text, lexicon=None) -> str`

Only the hidden-space/whitespace pass — no spellfixing (see
sentence-stop spacing (see `space_sentences` below):

```python
from khmerthings import space_words

space_words("ខ្ញុំទៅ  ផ្សារ")
# 'ខ្ញុំ​ទៅ ផ្សារ'

space_words("សំរាប់ការងារ")   # variant spelling passed through untouched
# 'សំរាប់​ការងារ'
```

### `space_sentences(text) -> str`

Only the Khmer sentence-stop spacing pass — a pure string scan, no
tokenizer, no lexicon argument:

```python
from khmerthings import space_sentences

space_sentences("ខ្ញុំទៅផ្សារ ។ទិញត្រី")
# 'ខ្ញុំទៅផ្សារ។ ទិញត្រី'
```

### `normalize_text(text, lexicon=None) -> str`

Returns *text* (NFC-normalized) with known misspellings fixed, hidden
spaces placed at bare word boundaries, whitespace collapsed/trimmed, and
sentence-stop spacing tidied.

```python
from khmerthings import normalize_text

normalize_text("ខ្ញុំទៅ  ផ្សារ")
# 'ខ្ញុំ​ទៅ ផ្សារ'

normalize_text("ខ្ញុំទៅផ្សារ ។ទិញត្រី")
# 'ខ្ញុំ​ទៅ​ផ្សារ។ ទិញ​ត្រី'
```

`lexicon` defaults to the core `words` source, exactly like

```python
from khmerthings import Lexicon

normalize_text("សំរាប់", Lexicon(["សំរាប់"]))
# 'សំរាប់'   # caller's lexicon wins over the variants map, same as fix_spelling
```

## How it works

`normalize_text` is `space_sentences(space_words(fix_spelling(text, lexicon), lexicon))`.

1. `fix_spelling` tokenizes exactly like the [word breaker](word-breaker.md)
   does — greedy longest match over character clusters — but against the
   chosen lexicon *plus* the variant misspellings, so known misspellings
   surface as single tokens; each variant-map token (not a word of the
   caller's lexicon) is replaced by its canonical spelling.
2. `space_words` tokenizes the same way and rebuilds the text token by
   token. Whitespace tokens are buffered rather than emitted immediately,
   so the separator between two real tokens can be decided once both sides
   are known:
   - two adjacent word-type tokens (Khmer, Latin, number) with nothing
     between them get a single hidden space (U+200B); if a visible
     whitespace run already separated them, it collapses to a single
     visible space instead — it is never downgraded to hidden;
   - any other whitespace run collapses to a single visible space; no
     whitespace at all stays as no separator.
   Because a separator is only ever emitted *before* a token, whitespace at
   the very start or end of the line is simply never written — the trim
   happens for free.
3. `space_sentences` is a pure string scan over the result — no tokenizer,
   no lexicon involved. A lone ។ or ៕ (not adjacent to other punctuation)
   never has a separator before it, and always gets exactly one space
   after it, unless nothing but whitespace follows through the end of the
   text.

## Guarantees & limitations

- **Deterministic.** Same input, same output, every time. No models, no
  randomness, no network.
- **Idempotent.** Normalizing already-normalized text returns it unchanged
  — re-tokenizing sees single hidden spaces (kept as hidden, not collapsed
  to visible), single visible spaces, and no remaining variant spellings.
- **Conservative spelling fixes.** Only variants-map misspellings are ever
  rewritten; unknown words are left exactly as typed (see the
  internal spelling checker to find those).
- **Word-boundary accuracy scales with the dictionary**, same as the
  [word breaker](word-breaker.md) — unrecognized spans are kept intact as
  a single unit, never guessed at.
- **Repeated sentence stops are not collapsed.** The tokenizer merges
  adjacent punctuation of the same class into one token, so something like
  "។។" is treated as a single two-character punctuation span and the
  before/after spacing rules do not fire on it.
- **Only Khmer full stops (។, ៕) get sentence-stop spacing.** ASCII
  punctuation (`.`, `!`, `?`) and other Khmer punctuation (៖, ៗ, ៘, ៙, ៚)
  only get the general whitespace collapse rule, not the trim-before/
  space-after treatment.
- **`space_words` and `space_sentences` are independently usable.** They
  are library-level API refinements of the same tool, documented here
  rather than as new CLI subcommands — see the Python API section and the
  CLI's `--only` flag.

## Task recipes

| Goal | Do this |
|---|---|
| Clean up raw/pasted Khmer text | `khmerthings normalize in.txt > out.txt` |
| Normalize a string in Python | `normalize_text(text)` |
| Normalize informal/social-media text | `khmerthings normalize --include names,modern file.txt` |
| Prepare a corpus for line-breaking or search indexing | `khmerthings normalize corpus.txt > corpus.clean.txt` |
| Only re-space, skip sentence-stop tidying | `khmerthings normalize --only words file.txt` / `space_words(text)` |
| Only tidy sentence-stop spacing | `khmerthings normalize --only sentences file.txt` / `space_sentences(text)` |

## Related tools

  reuses, on its own with no re-spacing.
- [Word breaker](word-breaker.md) — the segmentation engine underneath,
  and the source of the `mark_boundaries` hidden-space convention.
  normalizing.
