import unicodedata

import pytest

from khmerthings.orthography import OrthographyIssueCode, validate_orthography


@pytest.mark.parametrize(
    "text",
    [
        "ក",
        "ឥ",
        "ក្រ",
        "ស្ត្រី",
        "ខ្ញុំ",
        "កម្ពុជា",
        "ស៊ី",
        "ក៌",
        "hello ២០២៦!",
        "",
    ],
)
def test_valid_text_has_no_issues(text: str) -> None:
    assert validate_orthography(text) == ()


@pytest.mark.parametrize(
    ("text", "code", "issue_text"),
    [
        ("្ក", OrthographyIssueCode.ORPHAN_COENG, "្"),
        ("ក្", OrthographyIssueCode.ORPHAN_COENG, "្"),
        ("ក្ឥ", OrthographyIssueCode.INVALID_COENG_FOLLOWER, "្ឥ"),
        ("ក្១", OrthographyIssueCode.INVALID_COENG_FOLLOWER, "្១"),
        ("ាក", OrthographyIssueCode.ORPHAN_MARK, "ា"),
        ("ំក", OrthographyIssueCode.ORPHAN_MARK, "ំ"),
        ("កាិ", OrthographyIssueCode.REPEATED_DEPENDENT_VOWEL, "ិ"),
        ("ក៉៊", OrthographyIssueCode.REPEATED_REGISTER_SHIFTER, "៊"),
        ("កា៉", OrthographyIssueCode.INVALID_MARK_ORDER, "៉"),
        ("កំា", OrthographyIssueCode.INVALID_MARK_ORDER, "ា"),
    ],
)
def test_reports_structural_issue(text: str, code: OrthographyIssueCode, issue_text: str) -> None:
    issues = validate_orthography(text)
    assert len(issues) == 1
    assert issues[0].code is code
    assert issues[0].text == issue_text


def test_offsets_reference_nfc_text_and_results_are_deterministic() -> None:
    text = "xក្ឥកាិ"
    nfc = unicodedata.normalize("NFC", text)
    issues = validate_orthography(text)
    assert issues == validate_orthography(text)
    keys = [(i.start, i.end, i.code.value) for i in issues]
    assert keys == sorted(keys)
    for issue in issues:
        assert nfc[issue.start : issue.end] == issue.text
