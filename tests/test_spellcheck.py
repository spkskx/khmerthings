import unicodedata

import pytest

from khmerthings.lexicon import Lexicon, load_variants
from khmerthings.spellcheck import (
    IssueKind,
    SpellIssue,
    check_spelling,
    check_unknown,
    check_variants,
    fix_spelling,
)

CLEAN_SENTENCE = "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ"
VARIANT_SENTENCE = "ខ្ញុំសំរាប់ការងារ"  # សំរាប់ is a variant of សម្រាប់


class TestCheckSpelling:
    def test_clean_text_has_no_issues(self) -> None:
        assert check_spelling(CLEAN_SENTENCE) == []

    def test_empty(self) -> None:
        assert check_spelling("") == []

    def test_non_khmer_ignored(self) -> None:
        assert check_spelling("Hello world 123 !?") == []

    def test_variant_reported_with_canonical(self) -> None:
        assert check_spelling(VARIANT_SENTENCE) == [
            SpellIssue("សំរាប់", IssueKind.VARIANT, 5, 11, ("សម្រាប់",))
        ]

    def test_variant_offsets_in_mixed_text(self) -> None:
        issues = check_spelling("Hello សំរាប់ 123")
        assert issues == [SpellIssue("សំរាប់", IssueKind.VARIANT, 6, 12, ("សម្រាប់",))]

    def test_unknown_reported_with_nearby_word(self) -> None:
        # ស្រឡាញ is ស្រឡាញ់ without the final ​sign — one cluster edit away.
        issues = check_spelling("ខ្ញុំស្រឡាញភាសាខ្មែរ")
        assert len(issues) == 1
        issue = issues[0]
        assert issue.kind is IssueKind.UNKNOWN
        assert issue.text == "ស្រឡាញ"
        assert (issue.start, issue.end) == (5, 11)
        assert "ស្រឡាញ់" in issue.suggestions

    def test_issues_ordered_by_position(self) -> None:
        issues = check_spelling("សំរាប់ កំរិត")
        assert [i.text for i in issues] == ["សំរាប់", "កំរិត"]
        assert [i.kind for i in issues] == [IssueKind.VARIANT, IssueKind.VARIANT]
        assert issues[0].start < issues[1].start

    def test_variant_detected_with_custom_lexicon(self) -> None:
        lex = Lexicon(["ខ្ញុំ"])
        issues = check_spelling("សំរាប់", lex)
        assert issues == [SpellIssue("សំរាប់", IssueKind.VARIANT, 0, 6, ("សម្រាប់",))]

    def test_caller_lexicon_overrides_variant(self) -> None:
        # If the caller's lexicon lists the spelling as a word, it is not
        # flagged — the caller's lexicon wins over the built-in variants map.
        lex = Lexicon(["សំរាប់"])
        assert check_spelling("សំរាប់", lex) == []

    def test_deterministic(self) -> None:
        text = "ខ្ញុំសំរាបភាសា"
        assert check_spelling(text) == check_spelling(text)

    def test_equals_merged_check_variants_and_check_unknown(self) -> None:
        text = "សំរាប់ ស្រឡាញ"  # a variant plus an unknown span
        merged = sorted(check_variants(text) + check_unknown(text), key=lambda i: i.start)
        assert check_spelling(text) == merged

    def test_issues_ordered_by_position_mixed_kinds(self) -> None:
        issues = check_spelling("សំរាប់ ស្រឡាញ")
        assert [i.kind for i in issues] == [IssueKind.VARIANT, IssueKind.UNKNOWN]
        assert issues[0].start < issues[1].start


class TestCheckVariants:
    def test_variant_reported_with_canonical(self) -> None:
        assert check_variants(VARIANT_SENTENCE) == [
            SpellIssue("សំរាប់", IssueKind.VARIANT, 5, 11, ("សម្រាប់",))
        ]

    def test_caller_lexicon_overrides_variant(self) -> None:
        lex = Lexicon(["សំរាប់"])
        assert check_variants("សំរាប់", lex) == []

    def test_variant_detected_with_custom_lexicon(self) -> None:
        lex = Lexicon(["ខ្ញុំ"])
        assert check_variants("សំរាប់", lex) == [
            SpellIssue("សំរាប់", IssueKind.VARIANT, 0, 6, ("សម្រាប់",))
        ]

    def test_clean_text_has_no_issues(self) -> None:
        assert check_variants(CLEAN_SENTENCE) == []

    def test_empty(self) -> None:
        assert check_variants("") == []

    def test_non_khmer_ignored(self) -> None:
        assert check_variants("Hello world 123 !?") == []

    def test_never_reports_unknown_issues(self) -> None:
        text = "ខ្ញុំស្រឡាញភាសាខ្មែរ"  # unknown span, not a variant
        assert check_variants(text) == []

    def test_deterministic(self) -> None:
        assert check_variants(VARIANT_SENTENCE) == check_variants(VARIANT_SENTENCE)


class TestCheckUnknown:
    def test_unknown_reported_with_nearby_word(self) -> None:
        issues = check_unknown("ខ្ញុំស្រឡាញភាសាខ្មែរ")
        assert len(issues) == 1
        issue = issues[0]
        assert issue.kind is IssueKind.UNKNOWN
        assert issue.text == "ស្រឡាញ"
        assert (issue.start, issue.end) == (5, 11)
        assert "ស្រឡាញ់" in issue.suggestions

    def test_ranked_by_distance_then_khmer_order(self) -> None:
        lex = Lexicon(["កខចឆ", "កខគជ", "កខគច"])
        issues = check_unknown("កខគង", lex)
        assert len(issues) == 1
        assert issues[0].suggestions == ("កខគច", "កខគជ", "កខចឆ")

    def test_max_suggestions_truncates(self) -> None:
        lex = Lexicon(["កខចឆ", "កខគជ", "កខគច"])
        issues = check_unknown("កខគង", lex, max_suggestions=1)
        assert issues[0].suggestions == ("កខគច",)

    def test_max_suggestions_zero(self) -> None:
        issues = check_unknown("ស្រឡាញ", max_suggestions=0)
        assert issues[0].suggestions == ()

    def test_long_unknown_span_gets_no_suggestions(self) -> None:
        lex = Lexicon(["ខ្ញុំ"])
        issues = check_unknown("កខគឃងចឆជឈញ", lex)
        assert len(issues) == 1
        assert issues[0].suggestions == ()

    def test_no_suggestion_when_nothing_is_close(self) -> None:
        lex = Lexicon(["ខ្ញុំ"])
        issues = check_unknown("សាលារៀន", lex)
        assert issues[0].suggestions == ()

    def test_never_reports_variant_issues(self) -> None:
        assert check_unknown(VARIANT_SENTENCE) == []

    def test_deterministic(self) -> None:
        text = "ខ្ញុំស្រឡាញភាសាខ្មែរ"
        assert check_unknown(text) == check_unknown(text)


class TestSuggestions:
    def test_ranked_by_distance_then_khmer_order(self) -> None:
        # Against កខគង: កខគច and កខគជ are 1 edit away (Khmer order ច < ជ),
        # កខចឆ is 2 edits away — distance ranks first, Khmer order breaks ties.
        lex = Lexicon(["កខចឆ", "កខគជ", "កខគច"])
        issues = check_spelling("កខគង", lex)
        assert len(issues) == 1
        assert issues[0].suggestions == ("កខគច", "កខគជ", "កខចឆ")

    def test_max_suggestions_truncates(self) -> None:
        lex = Lexicon(["កខចឆ", "កខគជ", "កខគច"])
        issues = check_spelling("កខគង", lex, max_suggestions=1)
        assert issues[0].suggestions == ("កខគច",)

    def test_max_suggestions_zero(self) -> None:
        issues = check_spelling("ស្រឡាញ", max_suggestions=0)
        assert issues[0].suggestions == ()

    def test_long_unknown_span_gets_no_suggestions(self) -> None:
        lex = Lexicon(["ខ្ញុំ"])
        # Ten single-consonant clusters: too long to be one misspelled word.
        issues = check_spelling("កខគឃងចឆជឈញ", lex)
        assert len(issues) == 1
        assert issues[0].kind is IssueKind.UNKNOWN
        assert issues[0].suggestions == ()

    def test_no_suggestion_when_nothing_is_close(self) -> None:
        lex = Lexicon(["ខ្ញុំ"])
        issues = check_spelling("សាលារៀន", lex)
        assert issues[0].suggestions == ()

    @pytest.mark.parametrize("text", ["ស្រឡាញ", "ភាសាា", "សាលារៀម"])
    def test_suggestions_are_never_variant_keys(self, text: str) -> None:
        variants = load_variants()
        for issue in check_spelling(text):
            assert all(s not in variants for s in issue.suggestions)


class TestFixSpelling:
    def test_fixes_variant_in_sentence(self) -> None:
        assert fix_spelling(VARIANT_SENTENCE) == "ខ្ញុំសម្រាប់ការងារ"

    def test_fixes_multiple_variants(self) -> None:
        assert fix_spelling("សំរាប់ កំរិត") == "សម្រាប់ កម្រិត"

    def test_unknown_words_left_untouched(self) -> None:
        text = "ខ្ញុំស្រឡាញភាសា"  # unknown span, not a known variant
        assert fix_spelling(text) == text

    def test_caller_lexicon_overrides_variant(self) -> None:
        lex = Lexicon(["សំរាប់"])
        assert fix_spelling("សំរាប់", lex) == "សំរាប់"

    @pytest.mark.parametrize(
        "text",
        [
            CLEAN_SENTENCE,
            "ថ្ងៃនេះ ខ្ញុំទៅផ្សារ ទិញត្រី ២ គីឡូ។",
            "Hello ពិភពលោក 123 ៤៥៦",
            "",
        ],
    )
    def test_clean_text_unchanged(self, text: str) -> None:
        assert fix_spelling(text) == unicodedata.normalize("NFC", text)

    @pytest.mark.parametrize("text", [VARIANT_SENTENCE, "សំរាប់ កំរិត", CLEAN_SENTENCE, ""])
    def test_idempotent(self, text: str) -> None:
        fixed = fix_spelling(text)
        assert fix_spelling(fixed) == fixed

    @pytest.mark.parametrize("text", [VARIANT_SENTENCE, "សំរាប់ កំរិត អោយ"])
    def test_fixed_text_has_no_variant_issues(self, text: str) -> None:
        issues = check_spelling(fix_spelling(text))
        assert all(i.kind is not IssueKind.VARIANT for i in issues)


class TestWholeVariantsMap:
    """Data-driven over variants.txt — the suite scales with the data file."""

    def test_every_variant_is_flagged_with_its_canonical(self) -> None:
        for variant, canonical in load_variants().items():
            issues = check_spelling(variant)
            assert len(issues) == 1, variant
            assert issues[0].kind is IssueKind.VARIANT, variant
            assert issues[0].text == variant
            assert issues[0].suggestions == (canonical,), variant

    def test_every_variant_is_fixed_to_its_canonical(self) -> None:
        for variant, canonical in load_variants().items():
            assert fix_spelling(variant) == canonical

    def test_every_canonical_is_clean(self) -> None:
        # Canonicals live in the core wordlist, so the default check passes.
        for canonical in load_variants().values():
            assert check_spelling(canonical) == []
