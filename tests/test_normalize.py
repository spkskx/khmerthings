import unicodedata

import pytest

from khmerthings.lexicon import Lexicon
from khmerthings.normalize import normalize_text

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
