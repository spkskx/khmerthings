import pytest

from khmerthings import romanize
from khmerthings.lexicon import load_lexicon, load_romanizations
from khmerthings.romanize import _romanize_word


class TestRuleEngine:
    """Rule-only romanization (no exception-lexicon lookup).

    A known-answer regression table for :func:`_romanize_word`. These pin the
    *rule engine's* contract; the exception-lexicon corrections for the words
    the rules get wrong are covered in :class:`TestExceptionOverrides`. Values
    are hand-verified; ``ស្ត vs ស្ដ``-style look-alikes are avoided.
    """

    @pytest.mark.parametrize(
        "word, latin",
        [
            # --- Initials + inherent vowel: 1st series -> "a", 2nd -> "o" ----
            ("ក", "ka"),
            ("ខ", "kha"),
            ("គ", "ko"),
            ("ឃ", "kho"),
            ("ង", "ngo"),
            ("ច", "cha"),
            ("ឆ", "chha"),
            ("ជ", "cho"),
            ("ញ", "nho"),
            ("ដ", "da"),
            ("ណ", "na"),
            ("ត", "ta"),
            ("ថ", "tha"),
            ("ទ", "to"),
            ("ន", "no"),
            ("ប", "ba"),
            ("ផ", "pha"),
            ("ព", "po"),
            ("ភ", "pho"),
            ("ម", "mo"),
            ("យ", "yo"),
            ("រ", "ro"),
            ("ល", "lo"),
            ("វ", "vo"),
            ("ស", "sa"),
            ("ហ", "ha"),
            ("ឡ", "la"),
            ("អ", "a"),
        ],
    )
    def test_initial_inherent(self, word: str, latin: str) -> None:
        assert _romanize_word(word) == latin

    @pytest.mark.parametrize(
        "word, latin",
        [
            # Dependent vowels read per register: ក (1st) vs គ (2nd).
            ("កា", "ka"),
            ("គា", "kea"),
            ("កិ", "ke"),
            ("គិ", "ki"),
            ("កី", "kei"),
            ("គី", "ki"),
            ("កឹ", "koe"),
            ("គឹ", "koe"),
            ("កុ", "ko"),
            ("គុ", "ku"),
            ("កូ", "kou"),
            ("គូ", "ku"),
            ("កួ", "kuo"),
            ("គួ", "kuo"),
            ("កើ", "kaeu"),
            ("គើ", "keu"),
            ("កៀ", "kie"),
            ("គៀ", "kie"),
            ("កេ", "ke"),
            ("គេ", "ke"),
            ("កែ", "kae"),
            ("គែ", "kae"),
            ("កៃ", "kai"),
            ("គៃ", "key"),
            ("កោ", "kao"),
            ("គោ", "kao"),
            ("កៅ", "kau"),
            ("គៅ", "kau"),
        ],
    )
    def test_dependent_vowel_by_register(self, word: str, latin: str) -> None:
        assert _romanize_word(word) == latin

    @pytest.mark.parametrize(
        "word, latin",
        [
            # A bare final consonant reads as a coda (ចា + C).
            ("ចាក", "chak"),
            ("ចាង", "chang"),
            ("ចាច", "chach"),
            ("ចាញ", "chanh"),
            ("ចាត", "chat"),
            ("ចាន", "chan"),
            ("ចាប", "chap"),
            ("ចាម", "cham"),
            ("ចាយ", "chay"),
            ("ចារ", "char"),
            ("ចាល", "chal"),
            ("ចាស", "chas"),
            # Real words with codas.
            ("ពេញ", "penh"),
            ("ចាន", "chan"),
        ],
    )
    def test_final_coda(self, word: str, latin: str) -> None:
        assert _romanize_word(word) == latin

    @pytest.mark.parametrize(
        "word, latin",
        [
            ("កំ", "kam"),  # nikahit -> nasal coda "m"
            ("បាំ", "bam"),
            ("ចាំ", "cham"),
            ("កះ", "kah"),  # reahmuk -> final "h"
            ("ក៉", "ka"),  # muusikatoan forces 1st series (already 1st here)
            ("គ៊", "ko"),  # triisap forces 2nd series (already 2nd here)
        ],
    )
    def test_signs(self, word: str, latin: str) -> None:
        assert _romanize_word(word) == latin

    @pytest.mark.parametrize(
        "word, latin",
        [
            # Subscripts form onset clusters. NOTE: the rule uses the *last*
            # onset consonant for register, which is inaccurate for
            # stop+sonorant clusters — see TestExceptionOverrides.
            ("ស្រី", "sri"),
            ("ក្រុង", "krung"),
            ("ភ្នំ", "phnom"),
            ("ខ្មែរ", "khmaer"),
            ("ស្ត្រី", "stri"),
        ],
    )
    def test_subscript_clusters(self, word: str, latin: str) -> None:
        assert _romanize_word(word) == latin

    @pytest.mark.parametrize(
        "word, latin",
        [
            # Independent vowels carry their own vowel and take no onset.
            ("ឥ", "e"),
            ("ឧ", "o"),
            ("ឪ", "ov"),
            ("ឫ", "rue"),
            ("ឯ", "ae"),
            ("ឱ", "ao"),
            ("ឳ", "au"),
        ],
    )
    def test_independent_vowels(self, word: str, latin: str) -> None:
        assert _romanize_word(word) == latin


class TestExceptionOverrides:
    """Words where the exception lexicon corrects a rule-engine mistake.

    The rule engine derives register from the *last* onset consonant, which
    is wrong for stop+sonorant clusters (ប្រ, ក្រ): it lets the sonorant flip
    the series. These common words are pinned to their conventional spelling
    via ``data/romanize.txt`` so the user-facing :func:`romanize` is correct.
    """

    @pytest.mark.parametrize(
        "word, rule_output, corrected",
        [
            ("ក្រុង", "krung", "krong"),  # city / municipality
            ("ប្រាំ", "bream", "pram"),  # "five" — the rule's "bream" is plainly wrong
            ("ខ្មែរ", "khmaer", "khmer"),  # established spelling
        ],
    )
    def test_exception_corrects_rule(self, word: str, rule_output: str, corrected: str) -> None:
        assert _romanize_word(word) == rule_output  # the raw rule (documented)
        assert romanize(word) == corrected  # the exception-corrected output


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
