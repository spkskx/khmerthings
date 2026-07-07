# Spellchecker (`khmerthings spellcheck`)

## What it does

Finds spelling problems in Khmer text, deterministically. Two kinds of
issue are reported:

- **`variant`** — a *known misspelling* from the hand-curated variants map
  (e.g. deprecated orthography like សំរាប់ for សម្រាប់). The canonical
  spelling is reported as the single suggestion.
- **`unknown`** — a Khmer span that matches no dictionary word. It gets up
  to N suggestions: dictionary words ranked by cluster-level edit distance,
  ties broken by Khmer dictionary order.

The checker only reports — it never modifies text. To rewrite known
misspellings automatically, use the [spellfixer](spellfix.md).

Both detection and suggestions are pure dictionary lookups, so the checker
gets better automatically every time the wordlists and the variants map
grow — no code changes needed.

## Quick start

```sh
pip install khmerthings            # library
uv tool install khmerthings       # or: global CLI
```

```sh
$ echo "ខ្ញុំសំរាប់ការងារ" | khmerthings spellcheck
<stdin>:1:6: variant: សំរាប់ -> សម្រាប់
```

```python
from khmerthings import check_spelling

check_spelling("ខ្ញុំសំរាប់ការងារ")
# [SpellIssue(text='សំរាប់', kind=<IssueKind.VARIANT: 'variant'>, start=5, end=11, suggestions=('សម្រាប់',))]
```

## CLI reference

```
khmerthings spellcheck [files ...] [--json] [--max-suggestions N] [--only {variants,unknown}] [--include modern,names,variants]
```

Every option, with a real example of its effect:

### Input: files, multiple files, or stdin

`files` is zero or more paths; `-` or no argument reads stdin. Lines are
checked one by one, files processed in order.

One line is printed per issue in grep style —
`source:line:column: kind: text -> suggestions` (column is 1-based; no
`->` part when there are no suggestions) — and the command **exits 1 when
any issue was found**, 0 when the text is clean:

```sh
$ printf 'សំរាប់ កំរិត\nខ្ញុំទៅផ្សារ\n' | khmerthings spellcheck
<stdin>:1:1: variant: សំរាប់ -> សម្រាប់
<stdin>:1:8: variant: កំរិត -> កម្រិត
$ echo $?
1
```

### `--json` — machine-readable issues

Emits all issues as one JSON array (empty array when clean; the exit code
still tells clean from dirty). `start`/`end` are 0-based character offsets
into the NFC-normalized line; `col` is `start + 1`:

```sh
$ echo "ខ្ញុំស្រឡាញភាសាខ្មែរ" | khmerthings spellcheck --json
[
  {
    "source": "<stdin>",
    "line": 1,
    "col": 6,
    "start": 5,
    "end": 11,
    "text": "ស្រឡាញ",
    "kind": "unknown",
    "suggestions": [
      "ស្រឡាញ់"
    ]
  }
]
```

### `--max-suggestions N` — cap suggestions per unknown word

Default is 3. `0` disables suggestions entirely (fastest):

```sh
$ echo "ខ្ញុំស្រឡាញភាសាខ្មែរ" | khmerthings spellcheck --max-suggestions 1
<stdin>:1:6: unknown: ស្រឡាញ -> ស្រឡាញ់
```

### `--only {variants,unknown}` — restrict to one issue kind

`variants` is the fast path: a pure dictionary lookup, no edit-distance
search, so `--max-suggestions` has no visible effect with it (a variant
issue always has exactly one suggestion, the canonical spelling). `unknown`
runs only the edit-distance search:

```sh
$ echo "ខ្ញុំសំរាប់ការងារ" | khmerthings spellcheck --only variants
<stdin>:1:6: variant: សំរាប់ -> សម្រាប់
$ echo "ខ្ញុំស្រឡាញភាសាខ្មែរ" | khmerthings spellcheck --only unknown
<stdin>:1:6: unknown: ស្រឡាញ -> ស្រឡាញ់
```

### `--include modern,names,variants` — accept extra wordlists

The core vocabulary is always active; `--include` adds the extra built-in
wordlists (comma-separated) to what counts as *correctly spelled*. This is
the main lever against false positives on names and informal text:

```sh
$ echo "សុខា" | khmerthings spellcheck
<stdin>:1:1: unknown: សុខា -> សុក្រ
$ echo "សុខា" | khmerthings spellcheck --include names
$ echo $?
0
```

(Including `variants` makes the misspellings themselves count as words for
*segmentation* purposes only — they are still flagged.)

### Exit codes & errors

- `0` — text is clean.
- `1` — at least one issue was found (nothing on stderr), **or** an input
  file could not be read; then a one-line message goes to stderr:
  `khmerthings: error: [Errno 2] No such file or directory: '...'`
- `2` — bad usage (unknown flag, unknown `--include` source); argparse
  prints the usage message to stderr.

Scripts should treat exit 1 with empty stderr as "misspellings found" and
exit 1 with a `khmerthings: error:` line on stderr as an I/O failure.

## Python API

### `check_variants(text, lexicon=None) -> list[SpellIssue]`

The fast path: only `VARIANT` issues, pure dictionary lookup, no
edit-distance search. Useful when you don't need unknown-word suggestions
and want to skip their cost entirely:

```python
from khmerthings import check_variants

check_variants("ខ្ញុំសំរាប់ការងារ")
# [SpellIssue(text='សំរាប់', kind=<IssueKind.VARIANT: 'variant'>, start=5, end=11, suggestions=('សម្រាប់',))]

check_variants("ខ្ញុំស្រឡាញភាសាខ្មែរ")   # unknown span, not a variant
# []
```

### `check_unknown(text, lexicon=None, *, max_suggestions=3) -> list[SpellIssue]`

Only `UNKNOWN` issues — the expensive path, since every unmatched span is
edit-distance-searched against the whole lexicon:

```python
from khmerthings import check_unknown

check_unknown("ខ្ញុំស្រឡាញភាសាខ្មែរ")
# [SpellIssue(text='ស្រឡាញ', kind=<IssueKind.UNKNOWN: 'unknown'>, start=5, end=11, suggestions=('ស្រឡាញ់',))]

check_unknown("ខ្ញុំសំរាប់ការងារ")   # a variant, not unknown
# []
```

### `check_spelling(text, lexicon=None, *, max_suggestions=3) -> list[SpellIssue]`

A thin wrapper merging `check_variants` and `check_unknown`, sorted by
position. Returns all spelling issues in `text`, in order of appearance.
Non-Khmer text (Latin, digits, punctuation) is ignored. Clean or empty
input returns `[]`.

```python
from khmerthings import check_spelling

check_spelling("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ")     # correctly spelled
# []

check_spelling("ខ្ញុំស្រឡាញភាសាខ្មែរ")      # ស្រឡាញ dropped the ់
# [SpellIssue(text='ស្រឡាញ', kind=<IssueKind.UNKNOWN: 'unknown'>, start=5, end=11, suggestions=('ស្រឡាញ់',))]
```

`SpellIssue` is a frozen dataclass: `text` (the flagged span), `kind`
(`IssueKind.VARIANT` or `IssueKind.UNKNOWN`), `start`/`end` (character
offsets into the NFC-normalized input, same convention as `Token`), and
`suggestions` (a tuple — the canonical spelling for a variant, nearest
dictionary words for an unknown, possibly empty).

`lexicon` defaults to the core `words` source; pass
`load_lexicon("words", "names", "modern")` or your own `Lexicon` to widen
what counts as correct:

```python
from khmerthings import load_lexicon

check_spelling("សុខា", load_lexicon("words", "names", "modern"))
# []
```

The built-in variants map is always consulted on top of `lexicon` — even a
tiny custom lexicon still catches known misspellings:

```python
from khmerthings import Lexicon

check_spelling("សំរាប់", Lexicon(["ខ្ញុំ"]))
# [SpellIssue(text='សំរាប់', kind=<IssueKind.VARIANT: 'variant'>, start=0, end=6, suggestions=('សម្រាប់',))]
```

(Exception: if your lexicon itself lists the spelling as a word, your
lexicon wins and it is not flagged.)

`max_suggestions` caps suggestions per unknown issue (`0` disables them):

```python
check_spelling("ខ្ញុំស្រឡាញភាសាខ្មែរ", max_suggestions=1)
# [SpellIssue(text='ស្រឡាញ', kind=<IssueKind.UNKNOWN: 'unknown'>, start=5, end=11, suggestions=('ស្រឡាញ់',))]
```

## How it works

1. The text is Unicode NFC-normalized and tokenized exactly like the
   [word breaker](word-breaker.md) does — greedy longest match over
   character clusters — but against the chosen lexicon *plus* the variant
   misspellings, so known misspellings surface as single tokens.
2. Each Khmer token is classified: a variant-map entry (that your lexicon
   does not claim as a word) is a `variant` issue with its canonical
   spelling; an unmatched span is an `unknown` issue.
3. Suggestions for unknown spans are computed by Levenshtein edit distance
   measured in **character clusters** (not codepoints — dropping one
   diacritic is one edit), bounded by 1 for spans of up to 3 clusters and
   2 for longer spans, against every word of the lexicon. Candidates are
   ranked by distance, then Khmer dictionary order, and truncated to
   `max_suggestions`. Spans longer than 8 clusters get no suggestions —
   they are almost certainly several adjacent unknown words, not one
   misspelled word.
4. `check_spelling` is implemented as
   `sorted(check_variants(text, lexicon) + check_unknown(text, lexicon, max_suggestions=max_suggestions), key=lambda issue: issue.start)`
   — `check_variants` and `check_unknown` are independently callable when
   you only need one kind (e.g. skipping the edit-distance cost entirely
   with `check_variants`).

## Guarantees & limitations

- **Deterministic.** Same input, same output, every time. No models, no
  randomness, no network.
- **Read-only.** The checker never changes text; fixing is a separate,
  deliberately conservative tool ([spellfixer](spellfix.md)).
- **Accuracy scales with the data.** An `unknown` verdict means "not in
  the dictionary", which is only as good as dictionary coverage
  (1,895 entries across `words`/`names`/`modern` and growing) — expect
  false positives on names and slang unless you `--include names,modern`.
  Growing the wordlists and the variants map improves detection and
  suggestions with no code changes.
- **Suggestions are edit-distance neighbors, not context.** They are
  ranked by spelling similarity only; the tool never guesses from
  surrounding words, and multi-word unknown spans (over 8 clusters) get no
  suggestions.

## Task recipes

| Goal | Do this |
|---|---|
| Lint a file, fail CI on misspellings | `khmerthings spellcheck file.txt` (exit 1 = issues) |
| Check informal/social-media text | `khmerthings spellcheck --include names,modern file.txt` |
| Issues as data for another program | `khmerthings spellcheck --json file.txt` |
| Just detect, no suggestions (fastest) | `khmerthings spellcheck --max-suggestions 0 file.txt` |
| Fast misspelling-only check (no edit-distance cost) | `khmerthings spellcheck --only variants file.txt` / `check_variants(text)` |
| Check against a domain dictionary | `check_spelling(text, Lexicon.from_lines(open("domain.txt")))` |
| Find words to add to the lexicon | `khmerthings spellcheck --json corpus.txt \| jq -r '.[] \| select(.kind=="unknown") \| .text' \| sort -u` |

## Related tools

- [Spellfixer](spellfix.md) — auto-corrects the `variant` issues this tool
  reports.
- [Word breaker](word-breaker.md) — the segmentation engine underneath.
- [Word counter](word-counter.md) — counts unknown words per text
  (`unknown_khmer_words`), a quick coverage signal.
- [Line sorter](line-sorter.md) — the Khmer collation used to rank
  suggestions.
