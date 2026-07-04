# Spellfixer (`khmerthings spellfix`)

## What it does

Rewrites *known* Khmer misspellings to their canonical spelling — and
touches nothing else. The corrections come from the hand-curated variants
map (`misspelling → canonical`, e.g. deprecated orthography like
សំរាប់ → សម្រាប់), so every fix is a deliberate, human-verified mapping.

Unknown words are **never auto-fixed** — a word missing from the
dictionary is not proof it is wrong (it may be a name, slang, or simply
not curated yet). Use the [spellchecker](spellcheck.md) to *find* those
and decide yourself.

The fixer gets better automatically every time the variants map grows —
no code changes needed.

## Quick start

```sh
pip install khmerthings            # library
uv tool install khmerthings       # or: global CLI
```

```sh
$ echo "ខ្ញុំសំរាប់ការងារ" | khmerthings spellfix
ខ្ញុំសម្រាប់ការងារ
```

```python
from khmerthings import fix_spelling

fix_spelling("ខ្ញុំសំរាប់ការងារ")
# 'ខ្ញុំសម្រាប់ការងារ'
```

## CLI reference

```
khmerthings spellfix [files ...] [--include modern,names,variants]
```

Every option, with a real example of its effect:

### Input: files, multiple files, or stdin

`files` is zero or more paths; `-` or no argument reads stdin. Every input
line is printed back with known misspellings rewritten and everything else
untouched, files processed in order:

```sh
$ printf 'សំរាប់ កំរិត\nខ្ញុំទៅផ្សារ\n' | khmerthings spellfix
សម្រាប់ កម្រិត
ខ្ញុំទៅផ្សារ
```

Deprecated orthography is included in the map:

```sh
$ echo "អោយ" | khmerthings spellfix
ឱ្យ
```

### `--include modern,names,variants` — treat extra wordlists as correct

The core vocabulary is always active; `--include` adds the extra built-in
wordlists (comma-separated) to what counts as a correctly spelled word.
For the fixer this matters only in one edge case: a spelling listed both
in the variants map and in an included wordlist is treated as correct and
left alone (the wordlist wins). It is accepted for symmetry with the other
tools; typical usage needs no `--include`.

```sh
$ echo "សំរាប់" | khmerthings spellfix --include names,modern
សម្រាប់
```

### Exit codes & errors

- `0` — success (whether or not anything was rewritten).
- `1` — an input file could not be read; a one-line message goes to stderr:
  `khmerthings: error: [Errno 2] No such file or directory: '...'`
- `2` — bad usage (unknown flag, unknown `--include` source); argparse
  prints the usage message to stderr.

To know whether a text *needed* fixing, run the
[spellchecker](spellcheck.md) — its exit code distinguishes clean (0) from
dirty (1).

## Python API

### `fix_spelling(text, lexicon=None) -> str`

Returns `text` (NFC-normalized) with every known misspelling replaced by
its canonical spelling. Unknown words, correct words, and non-Khmer text
are copied verbatim; on clean text the result is exactly the NFC input.
Idempotent.

```python
from khmerthings import fix_spelling

fix_spelling("ខ្ញុំសំរាប់ការងារ")
# 'ខ្ញុំសម្រាប់ការងារ'

fix_spelling("ខ្ញុំស្រឡាញភាសា")     # unknown word: reported by check_spelling, never rewritten
# 'ខ្ញុំស្រឡាញភាសា'
```

`lexicon` defaults to the core `words` source and defines what counts as
an already-correct word. If your lexicon itself lists a variants-map
spelling as a word, your lexicon wins and it is left alone:

```python
from khmerthings import Lexicon

fix_spelling("សំរាប់", Lexicon(["សំរាប់"]))
# 'សំរាប់'
```

### The correction table: `load_variants()`

The variants map is a plain dict you can inspect or use directly:

```python
from khmerthings import load_variants

load_variants()["ព័ត៍មាន"]
# 'ព័ត៌មាន'
```

## How it works

1. The text is Unicode NFC-normalized and tokenized exactly like the
   [word breaker](word-breaker.md) does — greedy longest match over
   character clusters — but against the chosen lexicon *plus* the variant
   misspellings, so known misspellings surface as single tokens.
2. The text is rebuilt from the tokens: a token that is a variants-map
   entry (and not a word of the lexicon) is replaced by its canonical
   spelling; every other token is copied through unchanged.

## Guarantees & limitations

- **Deterministic.** Same input, same output, every time. No models, no
  randomness, no network.
- **Conservative and lossless elsewhere.** Only spans in the hand-curated
  variants map are ever rewritten; every other character passes through
  unchanged, so clean text round-trips exactly (NFC-normalized).
- **Idempotent.** Fixing already-fixed text changes nothing.
- **Fixes scale with the data.** Only mapped misspellings are corrected;
  growing `variants.txt` (and the wordlists that segmentation relies on)
  adds fixes with no code changes. Misspellings the map does not know
  surface as `unknown` issues in the [spellchecker](spellcheck.md)
  instead.

## Task recipes

| Goal | Do this |
|---|---|
| Auto-correct known misspellings | `khmerthings spellfix in.txt > out.txt` |
| Fix a string in Python | `fix_spelling(text)` |
| Fix, then review what is still unknown | `khmerthings spellfix f.txt \| khmerthings spellcheck` |
| Normalize a corpus before indexing | `khmerthings spellfix corpus.txt > corpus.fixed.txt` |
| See every correction the tool can make | `python -c "from khmerthings import load_variants; [print(v, '->', c) for v, c in load_variants().items()]"` |

## Related tools

- [Spellchecker](spellcheck.md) — reports what this tool fixes, plus
  unknown words it deliberately leaves alone.
- [Word breaker](word-breaker.md) — the segmentation engine underneath.
- [Line sorter](line-sorter.md) — Khmer dictionary-order sorting.
