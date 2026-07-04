# Security Policy

## Supported Versions

khmerthings is pre-1.0 and moves quickly. Only the latest release on PyPI
is supported with security fixes.

| Version | Supported |
|---|---|
| latest | :white_check_mark: |
| older  | :x:                |

## Reporting a Vulnerability

Please do **not** open a public GitHub issue for security vulnerabilities.

Instead, email **spksk@protonmail.com** with:

- A description of the vulnerability and its potential impact
- Steps to reproduce (proof-of-concept input, if applicable)
- Any suggested remediation

You should receive a response within a few days. Once a fix is confirmed,
it will be released as a patch version and noted in `CHANGELOG.md`
(credited if you'd like).

## Scope notes

khmerthings has zero runtime dependencies, does no network I/O, and does
no dynamic code execution — its main attack surface is malformed or
adversarial text input to the tokenizer/segmenter/lexicon code. Reports
about crashes, hangs, or resource exhaustion on untrusted input are welcome
and in scope.
