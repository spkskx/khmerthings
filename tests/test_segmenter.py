import unicodedata

import pytest

from khmerthings.counter import count_words
from khmerthings.lexicon import Lexicon
from khmerthings.segmenter import break_words, mark_boundaries

ZWSP = "​"


class TestBreakWords:
    def test_khmer_sentence(self) -> None:
        assert break_words("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ") == ["ខ្ញុំ", "ស្រឡាញ់", "ភាសា", "ខ្មែរ"]

    def test_mixed_scripts(self) -> None:
        assert break_words("ខ្ញុំ love ១២៣ 456។") == ["ខ្ញុំ", "love", "១២៣", "456"]

    def test_punctuation_and_space_excluded(self) -> None:
        assert break_words("។៕ ! ?") == []

    def test_empty(self) -> None:
        assert break_words("") == []

    def test_unknown_spans_included(self) -> None:
        lex = Lexicon(["ខ្ញុំ", "ទៅ"])
        assert break_words("ខ្ញុំសាលារៀនទៅ", lex) == ["ខ្ញុំ", "សាលារៀន", "ទៅ"]

    def test_zwsp_delimited(self) -> None:
        assert break_words("ខ្ញុំ​ទៅ​ផ្សារ") == ["ខ្ញុំ", "ទៅ", "ផ្សារ"]

    @pytest.mark.parametrize(
        "text",
        [
            "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ",
            "ថ្ងៃនេះ ខ្ញុំទៅផ្សារ ទិញត្រី ២ គីឡូ។",
            "Hello ពិភពលោក 123 ៤៥៦",
            "",
            "។៕",
        ],
    )
    def test_length_equals_count_words(self, text: str) -> None:
        assert len(break_words(text)) == count_words(text)


class TestMarkBoundaries:
    def test_inserts_zwsp_between_khmer_words(self) -> None:
        assert mark_boundaries("ខ្ញុំទៅផ្សារ") == f"ខ្ញុំ{ZWSP}ទៅ{ZWSP}ផ្សារ"

    def test_custom_separator(self) -> None:
        assert mark_boundaries("ខ្ញុំទៅ", separator="|") == "ខ្ញុំ|ទៅ"

    def test_existing_spacing_and_punct_preserved(self) -> None:
        text = "ខ្ញុំទៅ ផ្សារ។ OK!"
        assert mark_boundaries(text, separator="|") == "ខ្ញុំ|ទៅ ផ្សារ។ OK!"

    def test_no_separator_around_non_khmer(self) -> None:
        # Boundary insertion only happens between adjacent Khmer words.
        assert mark_boundaries("abcខ្ញុំ123", separator="|") == "abcខ្ញុំ123"

    def test_unknown_spans_get_boundaries(self) -> None:
        lex = Lexicon(["ខ្ញុំ", "ទៅ"])
        assert mark_boundaries("ខ្ញុំសាលាទៅ", separator="|", lexicon=lex) == "ខ្ញុំ|សាលា|ទៅ"

    def test_empty(self) -> None:
        assert mark_boundaries("") == ""

    @pytest.mark.parametrize(
        "text",
        [
            "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ",
            "ថ្ងៃនេះ ខ្ញុំទៅផ្សារ ទិញត្រី ២ គីឡូ។",
            "Hello ពិភពលោក 123 ៤៥៦",
            "",
        ],
    )
    def test_removing_separator_restores_input(self, text: str) -> None:
        marked = mark_boundaries(text, separator="\ue000")  # private-use, never in input
        assert marked.replace("\ue000", "") == unicodedata.normalize("NFC", text)

    def test_deterministic(self) -> None:
        text = "ខ្ញុំទៅសាលារៀនជាមួយមិត្ត"
        assert mark_boundaries(text) == mark_boundaries(text)
