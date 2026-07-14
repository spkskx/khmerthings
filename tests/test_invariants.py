"""Cross-module invariant sweep over a shared adversarial corpus.

Each individual module has its own invariant tests; this file runs one set of
deliberately nasty inputs — mixed scripts, zero-width spaces, orphan coeng,
stacked subscripts, sentence stops, digits, whitespace runs, and empty text —
through *every* structural guarantee at once. A regression in any layer that
these inputs happen to exercise surfaces here regardless of which module
changed.
"""

from __future__ import annotations

import unicodedata

import pytest

from khmerthings import (
    break_words,
    count_words,
    normalize_text,
    segment_clusters,
    tokenize,
)
from khmerthings.orthography import validate_orthography
from khmerthings.tokenizer import TokenType

#: Adversarial inputs shared by every invariant below.
CORPUS: list[str] = [
    "",
    " ",
    "\n\t  \n",
    "ក",
    "ខ្ញុំទៅសាលា",
    "ខ្ញុំ​ទៅ​សាលា",  # with zero-width spaces
    "ខ្ញុំចង់ទៅផ្សារនៅថ្ងៃស្អែក។",
    "កម្ពុជា​មាន​រាជធានី​ភ្នំពេញ។ គាត់​ជា​គ្រូ។",
    "hello ខ្មែរ ២០២៦ world!",
    "ការងារ​និង​ការសិក្សា",
    "ស្ត្រី​ខ្មែរ",  # stacked subscripts
    "១២៣៤៥៦៧៨៩០",
    "abc១២៣ការ។៕",
    "្ក",  # orphan coeng at start (malformed)
    "ក្",  # trailing coeng (malformed)
    "ក្ឥ",  # coeng before an independent vowel (malformed)
    "កាំះ",  # multiple signs
    "ﾟ ក ﷽",  # exotic non-Khmer that NFC may change
    "។ ។ ។",
]


@pytest.mark.parametrize("text", CORPUS)
def test_cluster_segmentation_is_lossless(text: str) -> None:
    assert "".join(segment_clusters(text)) == unicodedata.normalize("NFC", text)


@pytest.mark.parametrize("text", CORPUS)
def test_tokenization_is_lossless_and_contiguous(text: str) -> None:
    nfc = unicodedata.normalize("NFC", text)
    tokens = tokenize(text)
    assert "".join(t.text for t in tokens) == nfc
    # Offsets are contiguous, start at 0, cover the whole NFC input, and each
    # token's text matches the slice it claims.
    pos = 0
    for tok in tokens:
        assert tok.start == pos
        assert nfc[tok.start : tok.end] == tok.text
        pos = tok.end
    assert pos == len(nfc)


@pytest.mark.parametrize("text", CORPUS)
def test_token_boundaries_align_to_cluster_boundaries(text: str) -> None:
    # A lexicon match (and every token boundary) must never split a cluster.
    nfc = unicodedata.normalize("NFC", text)
    cluster_ends = set()
    offset = 0
    for cluster in segment_clusters(nfc):
        offset += len(cluster)
        cluster_ends.add(offset)
    cluster_ends.add(0)
    for tok in tokenize(text):
        assert tok.start in cluster_ends, f"token {tok!r} starts mid-cluster"
        assert tok.end in cluster_ends, f"token {tok!r} ends mid-cluster"


@pytest.mark.parametrize("text", CORPUS)
def test_word_count_matches_break_words(text: str) -> None:
    assert count_words(text) == len(break_words(text))


@pytest.mark.parametrize("text", CORPUS)
def test_normalize_is_idempotent(text: str) -> None:
    once = normalize_text(text)
    assert normalize_text(once) == once


@pytest.mark.parametrize("text", CORPUS)
def test_orthography_issues_have_stable_nfc_offsets(text: str) -> None:
    nfc = unicodedata.normalize("NFC", text)
    issues = validate_orthography(text)
    assert issues == validate_orthography(text)
    keys = [(issue.start, issue.end, issue.code.value) for issue in issues]
    assert keys == sorted(keys)
    for issue in issues:
        assert 0 <= issue.start < issue.end <= len(nfc)
        assert nfc[issue.start : issue.end] == issue.text


@pytest.mark.parametrize("text", CORPUS)
def test_khmer_word_tokens_are_nonempty_khmer(text: str) -> None:
    for tok in tokenize(text):
        if tok.type in (TokenType.KHMER_WORD, TokenType.KHMER_UNKNOWN):
            assert tok.text  # never an empty Khmer token
