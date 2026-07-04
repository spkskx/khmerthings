---
name: Bug report
about: Report incorrect or unexpected behavior from a khmerthings tool
title: "[bug] "
labels: bug
assignees: ""
---

## Which tool

<!-- e.g. count / segment / sort / spellcheck / spellfix / normalize -->

## What happened

<!-- What did you run, and what did you get back? -->

## Input

```
<!-- The exact Khmer text (or file) that triggers the issue. Paste as text,
     not a screenshot, so codepoints are preserved. -->
```

## Expected behavior

<!-- What should have happened instead? -->

## Command / code used

```sh
echo "..." | uv run khmerthings <subcommand> ...
```

## Environment

- khmerthings version: `uv run khmerthings --version` or `pip show khmerthings`
- Python version:
- OS:

## Additional context

<!-- Anything else — is this a lexicon gap (missing word), a segmentation
     bug, an invariant violation, etc.? -->
