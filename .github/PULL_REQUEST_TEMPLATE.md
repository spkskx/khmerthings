# Summary

<!-- What does this PR change, and why? -->

## Type of change

- [ ] New tool / feature
- [ ] Bug fix
- [ ] Lexicon update (`words.txt`)
- [ ] Tests / CI / tooling
- [ ] Documentation

## Checklist

- [ ] `uv run pytest` passes; new behavior is covered by tests
- [ ] `uv run mypy src tests` is clean
- [ ] `uv run ruff check` and `uv run ruff format --check` are clean
- [ ] Change is fully deterministic (no randomness, no ML/LLM inference)
- [ ] No third-party Khmer NLP code or data introduced; zero new runtime deps
- [ ] Lexicon edits (if any): NFC, Khmer-only, no duplicates, both ្ត/្ដ
      variants where applicable
- [ ] Public API changes re-exported in `__init__.py` and documented in
      `README.md` / `AGENTS.md`
- [ ] `CHANGELOG.md` updated under `[Unreleased]` (any user-visible change)
- [ ] Affected docs updated (`README.md`, `AGENTS.md`,
      `DEVELOPMENT_GUIDE.md`, docstrings)
