import unicodedata

import pytest

from khmerthings.clusters import segment_clusters


class TestBasicClusters:
    def test_bare_consonants(self) -> None:
        assert segment_clusters("កខគ") == ["ក", "ខ", "គ"]

    def test_consonant_with_vowel(self) -> None:
        assert segment_clusters("ការ") == ["កា", "រ"]

    def test_consonant_with_vowel_and_sign(self) -> None:
        # ញ់ = consonant + bantoc sign
        assert segment_clusters("ញ់") == ["ញ់"]

    def test_word_with_multiple_clusters(self) -> None:
        assert segment_clusters("ភាសា") == ["ភា", "សា"]

    def test_independent_vowel_is_a_base(self) -> None:
        assert segment_clusters("ឥឡូវ") == ["ឥ", "ឡូ", "វ"]


class TestSubscripts:
    def test_single_subscript(self) -> None:
        # ក្រ = ក + coeng + រ: one cluster
        assert segment_clusters("ក្រ") == ["ក្រ"]

    def test_double_subscript(self) -> None:
        # ស្ត្រី = ស + coeng ត + coeng រ + ី: one cluster
        assert segment_clusters("ស្ត្រី") == ["ស្ត្រី"]

    def test_khnhom(self) -> None:
        # ខ្ញុំ = ខ + coeng ញ + ុ + ំ: one cluster
        assert segment_clusters("ខ្ញុំ") == ["ខ្ញុំ"]

    def test_srolanh(self) -> None:
        assert segment_clusters("ស្រឡាញ់") == ["ស្រ", "ឡា", "ញ់"]

    def test_khmer_word(self) -> None:
        assert segment_clusters("ខ្មែរ") == ["ខ្មែ", "រ"]


class TestStandaloneClusters:
    def test_digits_are_standalone(self) -> None:
        assert segment_clusters("១២៣") == ["១", "២", "៣"]

    def test_punctuation_is_standalone(self) -> None:
        assert segment_clusters("ការ។") == ["កា", "រ", "។"]

    def test_non_khmer_characters_are_standalone(self) -> None:
        assert segment_clusters("abក") == ["a", "b", "ក"]

    def test_currency_sign(self) -> None:
        assert segment_clusters("៛") == ["៛"]


class TestMalformedInput:
    def test_trailing_orphan_coeng_attaches(self) -> None:
        assert segment_clusters("ក្") == ["ក្"]

    def test_leading_orphan_vowel_is_standalone(self) -> None:
        assert segment_clusters("ាក") == ["ា", "ក"]

    def test_orphan_vowel_after_digit_attaches(self) -> None:
        # Not linguistically valid, but must not crash or drop characters.
        result = segment_clusters("១ា")
        assert "".join(result) == "១ា"

    def test_coeng_before_non_base_stays_with_previous_cluster(self) -> None:
        result = segment_clusters("ក្១")
        assert "".join(result) == "ក្១"
        assert result[-1] == "១"

    def test_empty_string(self) -> None:
        assert segment_clusters("") == []


SAMPLE_TEXTS = [
    "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ",
    "សួស្តី! តើអ្នកសុខសប្បាយទេ?",
    "ថ្ងៃនេះ ខ្ញុំទៅផ្សារ ទិញត្រី ២ គីឡូ។",
    "Hello ពិភពលោក 123 ៤៥៦",
    "ព្រះរាជាណាចក្រកម្ពុជា",
    "ក្​ខ ្ា",  # deliberately malformed
    "",
    "   \t\n",
]


class TestInvariants:
    @pytest.mark.parametrize("text", SAMPLE_TEXTS)
    def test_lossless(self, text: str) -> None:
        assert "".join(segment_clusters(text)) == unicodedata.normalize("NFC", text)

    @pytest.mark.parametrize("text", SAMPLE_TEXTS)
    def test_deterministic(self, text: str) -> None:
        assert segment_clusters(text) == segment_clusters(text)

    @pytest.mark.parametrize("text", SAMPLE_TEXTS)
    def test_no_empty_clusters(self, text: str) -> None:
        assert all(segment_clusters(text))
