import unicodedata

import pytest

from khmerthings.lexicon import Lexicon
from khmerthings.normalize import normalize_text, space_sentences, space_words

ZWSP = "​"
VARIANT_SENTENCE = "ខ្ញុំសំរាប់ការងារ"  # សំរាប់ is a variant of សម្រាប់


class TestNormalizeText:
    def test_fixes_variant_inline(self) -> None:
        assert normalize_text(VARIANT_SENTENCE) == f"ខ្ញុំ{ZWSP}សម្រាប់{ZWSP}ការងារ"

    def test_inserts_zwsp_at_bare_word_boundary(self) -> None:
        assert normalize_text("ខ្ញុំទៅផ្សារ") == f"ខ្ញុំ{ZWSP}ទៅ{ZWSP}ផ្សារ"

    def test_existing_visible_space_preserved_not_downgraded(self) -> None:
        assert normalize_text("ខ្ញុំទៅ ផ្សារ") == f"ខ្ញុំ{ZWSP}ទៅ ផ្សារ"

    def test_multiple_spaces_collapsed(self) -> None:
        assert normalize_text("ខ្ញុំទៅ  ផ្សារ") == f"ខ្ញុំ{ZWSP}ទៅ ផ្សារ"
        assert normalize_text("Hello   world") == "Hello world"

    def test_leading_and_trailing_whitespace_trimmed(self) -> None:
        assert normalize_text("  ខ្ញុំទៅផ្សារ  ") == f"ខ្ញុំ{ZWSP}ទៅ{ZWSP}ផ្សារ"

    def test_space_trimmed_before_khan(self) -> None:
        assert normalize_text("ខ្ញុំទៅផ្សារ ។") == f"ខ្ញុំ{ZWSP}ទៅ{ZWSP}ផ្សារ។"

    def test_space_trimmed_before_bariyoosan(self) -> None:
        assert normalize_text("ខ្ញុំទៅផ្សារ ៕") == f"ខ្ញុំ{ZWSP}ទៅ{ZWSP}ផ្សារ៕"

    def test_space_forced_after_khan_even_when_jammed(self) -> None:
        assert normalize_text("ខ្ញុំទៅផ្សារ។ទិញត្រី") == f"ខ្ញុំ{ZWSP}ទៅ{ZWSP}ផ្សារ។ ទិញ{ZWSP}ត្រី"

    def test_space_after_khan_not_duplicated(self) -> None:
        assert normalize_text("ខ្ញុំទៅផ្សារ។ ទិញត្រី") == f"ខ្ញុំ{ZWSP}ទៅ{ZWSP}ផ្សារ។ ទិញ{ZWSP}ត្រី"

    def test_unknown_words_left_untouched(self) -> None:
        assert normalize_text("ស្រឡាញ") == "ស្រឡាញ"  # unknown span, not a variant

    def test_caller_lexicon_overrides_variant(self) -> None:
        lex = Lexicon(["សំរាប់"])
        assert normalize_text("សំរាប់", lex) == "សំរាប់"

    def test_empty(self) -> None:
        assert normalize_text("") == ""

    @pytest.mark.parametrize(
        "text",
        [
            VARIANT_SENTENCE,
            "ខ្ញុំទៅផ្សារ",
            "  ខ្ញុំទៅ  ផ្សារ។ទិញត្រី  ",
            "ថ្ងៃនេះ ខ្ញុំទៅផ្សារ ទិញត្រី ២ គីឡូ។",
            "Hello ពិភពលោក 123 ៤៥៦",
            "ខ្ញុំទៅផ្សារ។",
            "",
        ],
    )
    def test_idempotent(self, text: str) -> None:
        normalized = normalize_text(text)
        assert normalize_text(normalized) == normalized

    @pytest.mark.parametrize(
        "text",
        [
            "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ",
            "ថ្ងៃនេះ ខ្ញុំទៅផ្សារ ទិញត្រី ២ គីឡូ។",
            "Hello ពិភពលោក 123 ៤៥៦",
            "",
        ],
    )
    def test_normalizes_the_nfc_input(self, text: str) -> None:
        # Sanity: normalize_text never leaves behind non-NFC leftovers.
        result = normalize_text(text)
        assert result == unicodedata.normalize("NFC", result)

    def test_deterministic(self) -> None:
        text = "ខ្ញុំសំរាប់ការងារ។ទៅផ្សារ"
        assert normalize_text(text) == normalize_text(text)


class TestSpaceWords:
    def test_inserts_zwsp_at_bare_word_boundary(self) -> None:
        assert space_words("ខ្ញុំទៅផ្សារ") == f"ខ្ញុំ{ZWSP}ទៅ{ZWSP}ផ្សារ"

    def test_existing_visible_space_preserved_not_downgraded(self) -> None:
        assert space_words("ខ្ញុំទៅ ផ្សារ") == f"ខ្ញុំ{ZWSP}ទៅ ផ្សារ"

    def test_multiple_spaces_collapsed(self) -> None:
        assert space_words("ខ្ញុំទៅ  ផ្សារ") == f"ខ្ញុំ{ZWSP}ទៅ ផ្សារ"
        assert space_words("Hello   world") == "Hello world"

    def test_leading_and_trailing_whitespace_trimmed(self) -> None:
        assert space_words("  ខ្ញុំទៅផ្សារ  ") == f"ខ្ញុំ{ZWSP}ទៅ{ZWSP}ផ្សារ"

    def test_ignores_sentence_stop_suppression(self) -> None:
        # Unlike normalize_text/space_sentences, space_words never strips
        # whitespace around a sentence stop -- that's space_sentences's job.
        assert space_words("ផ្សារ ។") == "ផ្សារ ។"

    def test_does_not_fix_variant_spellings(self) -> None:
        assert space_words("សំរាប់ការងារ") == f"សំរាប់{ZWSP}ការងារ"

    def test_caller_lexicon_overrides_variant(self) -> None:
        lex = Lexicon(["សំរាប់"])
        assert space_words("សំរាប់", lex) == "សំរាប់"

    def test_empty(self) -> None:
        assert space_words("") == ""

    @pytest.mark.parametrize(
        "text",
        [
            "ខ្ញុំទៅផ្សារ",
            "ថ្ងៃនេះ ខ្ញុំទៅផ្សារ ទិញត្រី ២ គីឡូ",
            "Hello ពិភពលោក 123 ៤៥៦",
            "",
        ],
    )
    def test_idempotent(self, text: str) -> None:
        spaced = space_words(text)
        assert space_words(spaced) == spaced


class TestSpaceSentences:
    def test_space_trimmed_before_khan(self) -> None:
        assert space_sentences("ផ្សារ ។") == "ផ្សារ។"

    def test_space_trimmed_before_bariyoosan(self) -> None:
        assert space_sentences("ផ្សារ ៕") == "ផ្សារ៕"

    def test_space_forced_after_stop_even_when_jammed(self) -> None:
        assert space_sentences("ផ្សារ។ទិញ") == "ផ្សារ។ ទិញ"

    def test_space_after_stop_not_duplicated(self) -> None:
        assert space_sentences("ផ្សារ។ ទិញ") == "ផ្សារ។ ទិញ"

    def test_repeated_stops_not_collapsed(self) -> None:
        assert space_sentences("ផ្សារ។។ទិញ") == "ផ្សារ។។ទិញ"

    def test_ascii_punctuation_unaffected(self) -> None:
        assert space_sentences("ផ្សារ.ទិញ") == "ផ្សារ.ទិញ"

    def test_trailing_stop_no_forced_space_at_end_of_string(self) -> None:
        assert space_sentences("ផ្សារ។") == "ផ្សារ។"
        assert space_sentences("ផ្សារ។   ") == "ផ្សារ។"

    def test_no_lexicon_dependency(self) -> None:
        # space_sentences takes no lexicon argument at all.
        assert space_sentences("ផ្សារ ។") == "ផ្សារ។"

    def test_empty(self) -> None:
        assert space_sentences("") == ""

    def test_normalizes_nfc_input(self) -> None:
        text = "ថ្ងៃនេះ ខ្ញុំទៅផ្សារ ទិញត្រី ២ គីឡូ។"
        result = space_sentences(text)
        assert result == unicodedata.normalize("NFC", result)

    @pytest.mark.parametrize(
        "text",
        [
            "ផ្សារ ។",
            "ផ្សារ។ទិញ",
            "ផ្សារ។",
            "",
        ],
    )
    def test_idempotent(self, text: str) -> None:
        spaced = space_sentences(text)
        assert space_sentences(spaced) == spaced
