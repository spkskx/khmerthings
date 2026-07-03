import pytest

from khmerthings.counter import WordCount, analyze, count_words
from khmerthings.lexicon import Lexicon


class TestCountWords:
    def test_khmer_sentence(self) -> None:
        # ខ្ញុំ / ស្រឡាញ់ / ភាសា / ខ្មែរ
        assert count_words("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ") == 4

    def test_empty(self) -> None:
        assert count_words("") == 0

    def test_whitespace_only(self) -> None:
        assert count_words("  \t\n") == 0

    def test_punctuation_only(self) -> None:
        assert count_words("។៕!?") == 0

    def test_latin_words(self) -> None:
        assert count_words("hello beautiful world") == 3

    def test_mixed_scripts_and_digits(self) -> None:
        # Khmer: ខ្ញុំ មាន ឆ្កែ ក្បាល (4), numbers: ២ and 3 (2), Latin: and, cats (2)
        assert count_words("ខ្ញុំមានឆ្កែ ២ ក្បាល and 3 cats") == 8

    def test_khmer_digits_count_as_numbers(self) -> None:
        result = analyze("១២៣ 456")
        assert result.numbers == 2
        assert result.total_words == 2

    def test_zwsp_delimited_words(self) -> None:
        assert count_words("ខ្ញុំ​ទៅ​ផ្សារ") == 3


class TestAnalyze:
    def test_field_breakdown(self) -> None:
        result = analyze("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ hello 123")
        assert result == WordCount(
            total_words=6,
            khmer_words=4,
            unknown_khmer_words=0,
            latin_words=1,
            numbers=1,
            clusters=8,  # ខ្ញុំ(1) + ស្រ|ឡា|ញ់(3) + ភា|សា(2) + ខ្មែ|រ(2)
            khmer_characters=21,
            characters=31,
        )

    def test_empty_analysis(self) -> None:
        assert analyze("") == WordCount(0, 0, 0, 0, 0, 0, 0, 0)

    def test_khmer_character_and_cluster_counts(self) -> None:
        result = analyze("ខ្ញុំ")  # 5 codepoints, 1 cluster, 1 word
        assert result.khmer_characters == 5
        assert result.characters == 5
        assert result.clusters == 1
        assert result.total_words == 1

    def test_khmer_digit_clusters(self) -> None:
        result = analyze("១២៣")
        assert result.clusters == 3
        assert result.numbers == 1
        assert result.khmer_characters == 3

    def test_unknown_words_counted(self) -> None:
        lex = Lexicon(["ខ្ញុំ", "ទៅ"])
        result = analyze("ខ្ញុំសាលារៀនទៅ", lexicon=lex)
        assert result.khmer_words == 2
        assert result.unknown_khmer_words == 1
        assert result.total_words == 3

    def test_deterministic(self) -> None:
        text = "ថ្ងៃនេះ ខ្ញុំទៅផ្សារ ទិញត្រី ២ គីឡូ។ It cost $5."
        assert analyze(text) == analyze(text)

    def test_result_is_immutable(self) -> None:
        result = analyze("ខ្ញុំ")
        with pytest.raises(AttributeError):
            result.total_words = 99  # type: ignore[misc]
