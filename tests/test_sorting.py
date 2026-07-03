import pytest

from khmerthings.sorting import khmer_sort_key, sort_lines


class TestKhmerSortKey:
    def test_consonant_alphabet_order(self) -> None:
        # The Khmer consonant alphabet is in codepoint order.
        assert khmer_sort_key("ក") < khmer_sort_key("ខ") < khmer_sort_key("គ")
        assert khmer_sort_key("ស") < khmer_sort_key("ហ") < khmer_sort_key("អ")

    def test_dictionary_order_within_a_base(self) -> None:
        # ក < កក (prefix) < កា (vowel) < ក្រ (subscript comes last)
        words = ["ក្រ", "កា", "ក", "កក"]
        assert sort_lines(words) == ["ក", "កក", "កា", "ក្រ"]

    def test_vowel_entries_before_subscript_entries(self) -> None:
        # Naive codepoint sort would place ក្កោ before កៅ (coeng U+17D2 > ៅ U+17C5
        # is irrelevant: it compares ្ at index 1). Dictionary order wants all
        # vowel forms of the bare base before any subscript stack.
        assert khmer_sort_key("កៅ") < khmer_sort_key("ក្កោ")
        assert sorted(["ក្កោ", "កៅ"]) == ["កៅ", "ក្កោ"]  # naive sort is the opposite

    def test_subscript_groups_with_base(self) -> None:
        # ខ្ញុំ (base ខ) must sort under ខ, i.e. after every ក word.
        assert khmer_sort_key("កៅ") < khmer_sort_key("ខ្ញុំ")
        assert khmer_sort_key("ខាង") < khmer_sort_key("ខ្ញុំ")

    def test_dependent_vowel_order(self) -> None:
        # Dependent vowels are in codepoint (dictionary) order: ា < ិ < ុ < ៅ
        assert (
            khmer_sort_key("កា") < khmer_sort_key("កិ") < khmer_sort_key("កុ") < khmer_sort_key("កៅ")
        )

    def test_signs_sort_after_plain_vowel(self) -> None:
        assert khmer_sort_key("កា") < khmer_sort_key("កាំ")

    def test_non_khmer_falls_back_to_codepoints(self) -> None:
        assert khmer_sort_key("apple") < khmer_sort_key("banana")
        assert khmer_sort_key("ABC") < khmer_sort_key("abc")

    def test_ascii_sorts_before_khmer(self) -> None:
        assert khmer_sort_key("zebra") < khmer_sort_key("ក")

    def test_empty_string_sorts_first(self) -> None:
        assert khmer_sort_key("") < khmer_sort_key("a")
        assert khmer_sort_key("") < khmer_sort_key("ក")

    def test_total_order_tiebreak_on_text(self) -> None:
        # Malformed strings can share cluster keys; the raw text tiebreaker
        # must still give a deterministic, total order.
        a, b = "ក់ា", "កា់"
        assert khmer_sort_key(a) != khmer_sort_key(b)
        assert sort_lines([a, b]) == sort_lines([b, a])


class TestSortLines:
    def test_ascending_default(self) -> None:
        assert sort_lines(["ខ", "ក", "គ"]) == ["ក", "ខ", "គ"]

    def test_descending(self) -> None:
        assert sort_lines(["ខ", "ក", "គ"], descending=True) == ["គ", "ខ", "ក"]

    def test_desc_is_exact_reverse_of_asc(self) -> None:
        lines = ["ក្រ", "កា", "hello", "", "១២៣", "ខ្ញុំ", "Zebra"]
        assert sort_lines(lines, descending=True) == list(reversed(sort_lines(lines)))

    def test_duplicates_kept(self) -> None:
        assert sort_lines(["ក", "ក", "ខ"]) == ["ក", "ក", "ខ"]

    def test_mixed_scripts(self) -> None:
        assert sort_lines(["ខ្មែរ", "english", "ការងារ"]) == ["english", "ការងារ", "ខ្មែរ"]

    def test_empty_lines_sort_first(self) -> None:
        assert sort_lines(["ក", "", "a"]) == ["", "a", "ក"]

    def test_empty_input(self) -> None:
        assert sort_lines([]) == []

    def test_accepts_any_iterable(self) -> None:
        assert sort_lines(iter(["ខ", "ក"])) == ["ក", "ខ"]

    @pytest.mark.parametrize(
        "lines",
        [
            ["ខ្ញុំ", "កា", "ក្រ", "១", "។", "abc", ""],
            ["ស្រឡាញ់", "ស្រុក", "សាលា", "ស"],
        ],
    )
    def test_deterministic_and_permutation_independent(self, lines: list[str]) -> None:
        expected = sort_lines(lines)
        assert sort_lines(list(reversed(lines))) == expected
        assert sort_lines(expected) == expected  # idempotent
