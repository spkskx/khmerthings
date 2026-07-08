import pytest

from khmerthings import romanize
from khmerthings.lexicon import load_lexicon, load_romanizations
from khmerthings.romanize import _romanize_word


class TestRuleEngine:
    """Rule-only romanization (no exception-lexicon lookup)."""

    @pytest.mark.parametrize(
        "word, latin",
        [
            # Register: 1st-series ក vs 2nd-series គ change the inherent vowel.
            ("ក", "ka"),
            ("គ", "ko"),
            # Register also changes a following dependent vowel.
            ("កា", "ka"),
            ("គា", "kea"),
            ("កិ", "ke"),
            ("គិ", "ki"),
            # Subscript consonants form onset clusters.
            ("ស្រី", "sri"),
            ("ក្រុង", "krung"),
            # Final consonants read differently from initials (ញ -> nh coda).
            ("ភ្នំ", "phnom"),
            ("ពេញ", "penh"),
            ("ចាន", "chan"),
            ("ទឹក", "toek"),
            # Register shifter muusikatoan / passthrough of unknown-but-Khmer.
            ("ខ្មែរ", "khmaer"),
        ],
    )
    def test_word(self, word: str, latin: str) -> None:
        assert _romanize_word(word) == latin


class TestRomanize:
    def test_exception_lexicon_overrides_rules(self) -> None:
        # ភ្នំពេញ is in the exception lexicon; the rule engine alone would run
        # the syllables together without the conventional space.
        assert romanize("ភ្នំពេញ") == "phnom penh"
        assert romanize("ខ្មែរ") == "khmer"  # exception, not the rule "khmaer"

    def test_adjacent_khmer_words_are_space_separated(self) -> None:
        # Khmer writes no spaces between words; romanized words are separated.
        assert romanize("ខ្ញុំទៅសាលា") == "khnhum tau salea"

    def test_khmer_digits_become_arabic(self) -> None:
        assert romanize("២០២៦") == "2026"

    def test_non_khmer_passes_through(self) -> None:
        assert romanize("hello ២០២៦ ភ្នំពេញ") == "hello 2026 phnom penh"
        assert romanize("abc") == "abc"

    def test_empty(self) -> None:
        assert romanize("") == ""

    def test_khmer_punctuation_preserved(self) -> None:
        assert romanize("សាលា។") == "salea។"

    def test_unknown_khmer_word_is_still_romanized(self) -> None:
        # A made-up cluster run absent from every lexicon still gets rules.
        assert romanize("ក") == "ka"

    def test_include_extends_exception_tokenization(self) -> None:
        # Romanization is stable whether or not extra sources are included.
        assert romanize("ភ្នំពេញ", load_lexicon("words", "names")) == "phnom penh"


class TestExceptionData:
    def test_all_values_ascii_and_keys_khmer(self) -> None:
        mapping = load_romanizations()
        assert mapping  # non-empty
        for khmer, latin in mapping.items():
            assert latin == latin.strip() and latin.isascii()
            assert khmer  # keys validated as NFC Khmer by the loader
        assert mapping["ភ្នំពេញ"] == "phnom penh"
