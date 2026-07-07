import pytest

from khmerthings.condense import (
    DEFAULT_REMOVE,
    condense_text,
    content_tokens,
    content_words,
)
from khmerthings.lexicon import (
    STOPWORD_CATEGORIES,
    Lexicon,
    load_lexicon,
    load_stopwords,
)
from khmerthings.tokenizer import TokenType

ZWSP = "​"

# ខ្ញុំ(pron) ចង់(aux) ទៅ(content verb) ផ្សារ(content) នៅ(prep) ព្រោះ(conj) ...
SENTENCE = "ខ្ញុំចង់ទៅផ្សារនៅ ព្រោះខ្ញុំចង់ទិញត្រី"


class TestContentWords:
    def test_strips_default_function_words(self) -> None:
        # នៅ (preposition) and ព្រោះ (conjunction) are removed by default;
        # ខ្ញុំ (pronoun) and ចង់ (auxiliary) are kept — they carry intent.
        assert content_words(SENTENCE) == [
            "ខ្ញុំ",
            "ចង់",
            "ទៅ",
            "ផ្សារ",
            "ខ្ញុំ",
            "ចង់",
            "ទិញ",
            "ត្រី",
        ]

    def test_remove_extra_categories(self) -> None:
        got = content_words(SENTENCE, remove=DEFAULT_REMOVE | {"pronoun", "auxiliary"})
        assert got == ["ទៅ", "ផ្សារ", "ទិញ", "ត្រី"]

    def test_remove_empty_keeps_everything_but_punct(self) -> None:
        assert content_words("ខ្ញុំទៅ។", remove=frozenset()) == ["ខ្ញុំ", "ទៅ"]

    def test_keeps_unknown_latin_and_numbers(self) -> None:
        assert content_words("ខ្ញុំ Facebook 2024 ស្រឡាញ") == [
            "ខ្ញុំ",
            "Facebook",
            "2024",
            "ស្រឡាញ",  # unknown Khmer span, kept
        ]

    def test_punctuation_and_space_dropped(self) -> None:
        assert content_words("ផ្សារ, ត្រី។") == ["ផ្សារ", "ត្រី"]

    def test_stopword_inside_lexicon_compound_is_not_split(self) -> None:
        # ថ្ងៃនេះ ("today") is a single lexicon word; the នេះ inside it is not
        # a separate token, so it survives as one content word.
        assert content_words("ថ្ងៃនេះ") == ["ថ្ងៃនេះ"]

    def test_empty(self) -> None:
        assert content_words("") == []

    def test_unknown_category_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown stopword categor"):
            content_words("ខ្ញុំ", remove={"bogus"})


class TestContentTokens:
    def test_returns_typed_tokens(self) -> None:
        tokens = content_tokens("ខ្ញុំ Facebook")
        assert [(t.text, t.type) for t in tokens] == [
            ("ខ្ញុំ", TokenType.KHMER_WORD),
            ("Facebook", TokenType.LATIN),
        ]

    def test_offsets_index_into_input(self) -> None:
        (tok,) = content_tokens("នៅផ្សារ")  # នៅ dropped, ផ្សារ kept
        assert "នៅផ្សារ"[tok.start : tok.end] == "ផ្សារ"


class TestCondenseText:
    def test_joins_khmer_words_with_zwsp(self) -> None:
        assert condense_text("ខ្ញុំចង់ទៅផ្សារនៅ") == f"ខ្ញុំ{ZWSP}ចង់{ZWSP}ទៅ{ZWSP}ផ្សារ"

    def test_space_between_khmer_and_latin(self) -> None:
        assert condense_text("ខ្ញុំ Facebook") == "ខ្ញុំ Facebook"

    def test_empty(self) -> None:
        assert condense_text("") == ""

    def test_all_function_words_condense_to_empty(self) -> None:
        assert condense_text("នៅ ព្រោះ និង") == ""


class TestCallerLexicon:
    def test_stopword_recognized_even_with_minimal_lexicon(self) -> None:
        # Passing a lexicon that lacks នៅ must not stop it being removed:
        # content_tokens unions the stopwords into the tokenizing lexicon.
        lex = Lexicon(["ផ្សារ"])
        assert content_words("នៅផ្សារ", lex) == ["ផ្សារ"]


class TestStopwordDataInvariants:
    def test_every_stopword_is_a_real_word(self) -> None:
        # A stopword must be an actual word in the shipped lexicon, not a new
        # spelling introduced only to strip it.
        lexicon = load_lexicon("words", "names", "modern")
        missing = [w for w in load_stopwords() if w not in lexicon]
        assert missing == []

    def test_all_categories_are_known(self) -> None:
        assert set(load_stopwords().values()) <= STOPWORD_CATEGORIES

    def test_default_remove_is_subset_of_categories(self) -> None:
        assert DEFAULT_REMOVE <= STOPWORD_CATEGORIES

    def test_intent_categories_kept_by_default(self) -> None:
        assert not ({"pronoun", "auxiliary", "question"} & DEFAULT_REMOVE)
