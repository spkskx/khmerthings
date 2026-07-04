# Contributing

Thanks for considering a contribution to khmerthings.

This project has hard, non-negotiable constraints — read
[AGENTS.md](AGENTS.md) (agent-oriented) or
[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) (human-oriented) before
opening a PR:

- **Deterministic only** — rule/algorithm/dictionary-based, no ML/LLM
  inference at runtime.
- **Self-owned word data** — no bulk-imported wordlists or third-party
  Khmer NLP code; entries are curated and verified individually.
- **Zero runtime dependencies** — stdlib only; dev tooling is the only
  exception.
- **Tests first** — every behavior change ships with tests.

## Setup

```sh
git clone git@github.com:spkskx/khmerthings.git
cd khmerthings
uv sync
```

## Before opening a PR

```sh
uv run pytest                # tests must pass
uv run mypy src tests        # strict type check must be clean
uv run ruff check --fix && uv run ruff format   # lint + format
```

All four checks run in CI on every PR and must be green to merge.

Also update, as applicable: the per-tool doc in `docs/<tool>.md` (with real,
executed example output — never invented), `README.md`, `AGENTS.md`,
`DEVELOPMENT_GUIDE.md`, and `CHANGELOG.md` under `[Unreleased]`. The PR
template checklist covers the full list.

## Adding or editing wordlist entries

See the "Editing the wordlists" section of
[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md#editing-the-wordlists-srckhmerthingsdata)
for which file an entry belongs in, formatting rules, and the
misspelling→canonical (`variants.txt`) conventions. Do not include notes
about where a word or name candidate came from — data provenance is
intentionally never documented in this repo.

## Reporting bugs / requesting features

Use the issue templates. For security issues, do **not** open a public
issue — see [SECURITY.md](SECURITY.md).

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
