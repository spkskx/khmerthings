import pytest

from khmerthings.numerals import arabic_to_khmer, khmer_to_arabic, number_to_words


class TestDigits:
    @pytest.mark.parametrize(
        "arabic, khmer",
        [
            ("0123456789", "០១២៣៤៥៦៧៨៩"),
            ("A320", "A៣២០"),
            ("no digits", "no digits"),
            ("", ""),
            ("2026", "២០២៦"),
        ],
    )
    def test_arabic_to_khmer(self, arabic: str, khmer: str) -> None:
        assert arabic_to_khmer(arabic) == khmer

    @pytest.mark.parametrize(
        "arabic, khmer",
        [
            ("0123456789", "០១២៣៤៥៦៧៨៩"),
            ("A320", "A៣២០"),
            ("no digits", "no digits"),
            ("", ""),
        ],
    )
    def test_khmer_to_arabic(self, arabic: str, khmer: str) -> None:
        assert khmer_to_arabic(khmer) == arabic

    def test_roundtrip_on_digit_subset(self) -> None:
        text = "0123456789"
        assert khmer_to_arabic(arabic_to_khmer(text)) == text
        assert arabic_to_khmer(khmer_to_arabic("០១២៣៤៥៦៧៨៩")) == "០១២៣៤៥៦៧៨៩"

    def test_non_digits_pass_through_unchanged(self) -> None:
        mixed = "តម្លៃ 1,234.50 ដុល្លារ"
        assert arabic_to_khmer(mixed) == "តម្លៃ ១,២៣៤.៥០ ដុល្លារ"


class TestNumberToWords:
    @pytest.mark.parametrize(
        "n, words",
        [
            (0, "សូន្យ"),
            (1, "មួយ"),
            (5, "ប្រាំ"),
            (9, "ប្រាំបួន"),
            (10, "ដប់"),
            (11, "ដប់មួយ"),
            (19, "ដប់ប្រាំបួន"),
            (20, "ម្ភៃ"),
            (21, "ម្ភៃមួយ"),
            (30, "សាមសិប"),
            (99, "កៅសិបប្រាំបួន"),
            (100, "មួយរយ"),
            (101, "មួយរយមួយ"),
            (123, "មួយរយម្ភៃបី"),
            (1000, "មួយពាន់"),
            (1234, "មួយពាន់ពីររយសាមសិបបួន"),
            (10_000, "មួយម៉ឺន"),
            (100_000, "មួយសែន"),
            (1_000_000, "មួយលាន"),
            (10_000_000, "ដប់លាន"),
            (-5, "ដកប្រាំ"),
        ],
    )
    def test_spellings(self, n: int, words: str) -> None:
        assert number_to_words(n) == words
