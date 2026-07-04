import unicodedata

import pytest

from khmerthings.lexicon import Lexicon
from khmerthings.tokenizer import Token, TokenType, tokenize


def types_and_texts(tokens: list[Token]) -> list[tuple[TokenType, str]]:
    return [(t.type, t.text) for t in tokens]


class TestKhmerSegmentation:
    def test_simple_sentence(self) -> None:
        tokens = tokenize("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ")
        assert types_and_texts(tokens) == [
            (TokenType.KHMER_WORD, "ខ្ញុំ"),
            (TokenType.KHMER_WORD, "ស្រឡាញ់"),
            (TokenType.KHMER_WORD, "ភាសា"),
            (TokenType.KHMER_WORD, "ខ្មែរ"),
        ]

    def test_greedy_longest_match(self) -> None:
        lex = Lexicon(["កា", "ការ", "ការងារ", "ងារ"])
        tokens = tokenize("ការងារ", lex)
        assert types_and_texts(tokens) == [(TokenType.KHMER_WORD, "ការងារ")]

    def test_unknown_run_is_one_token(self) -> None:
        lex = Lexicon(["ខ្ញុំ", "ទៅ"])
        tokens = tokenize("ខ្ញុំសាលារៀនទៅ", lex)
        assert types_and_texts(tokens) == [
            (TokenType.KHMER_WORD, "ខ្ញុំ"),
            (TokenType.KHMER_UNKNOWN, "សាលារៀន"),
            (TokenType.KHMER_WORD, "ទៅ"),
        ]

    def test_fully_unknown_run(self) -> None:
        lex = Lexicon(["ខ្ញុំ"])
        tokens = tokenize("ភាសា", lex)
        assert types_and_texts(tokens) == [(TokenType.KHMER_UNKNOWN, "ភាសា")]

    def test_zwsp_separates_words(self) -> None:
        tokens = tokenize("ខ្ញុំ​ទៅ")
        assert types_and_texts(tokens) == [
            (TokenType.KHMER_WORD, "ខ្ញុំ"),
            (TokenType.SPACE, "​"),
            (TokenType.KHMER_WORD, "ទៅ"),
        ]


class TestScriptRuns:
    def test_mixed_text(self) -> None:
        tokens = tokenize("ខ្ញុំ love ១២៣ 456។")
        assert types_and_texts(tokens) == [
            (TokenType.KHMER_WORD, "ខ្ញុំ"),
            (TokenType.SPACE, " "),
            (TokenType.LATIN, "love"),
            (TokenType.SPACE, " "),
            (TokenType.KHMER_DIGIT, "១២៣"),
            (TokenType.SPACE, " "),
            (TokenType.NUMBER, "456"),
            (TokenType.PUNCT, "។"),
        ]

    def test_khmer_punctuation(self) -> None:
        tokens = tokenize("ភាសា។៕")
        assert types_and_texts(tokens) == [
            (TokenType.KHMER_WORD, "ភាសា"),
            (TokenType.PUNCT, "។៕"),
        ]

    def test_latin_includes_accented_letters(self) -> None:
        tokens = tokenize("café")
        assert types_and_texts(tokens) == [(TokenType.LATIN, "café")]

    def test_other_category(self) -> None:
        tokens = tokenize("៛")
        assert types_and_texts(tokens) == [(TokenType.OTHER, "៛")]

    def test_empty_input(self) -> None:
        assert tokenize("") == []

    def test_whitespace_only(self) -> None:
        tokens = tokenize(" \t\n")
        assert types_and_texts(tokens) == [(TokenType.SPACE, " \t\n")]


SAMPLE_TEXTS = [
    "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ",
    "សួស្តី! តើអ្នកសុខសប្បាយទេ?",
    "ថ្ងៃនេះ ខ្ញុំទៅផ្សារ ទិញត្រី ២ គីឡូ។",
    "Hello ពិភពលោក 123 ៤៥៦ ៛",
    "ខ្ញុំ​ទៅ​សាលា",
    "",
]


class TestInvariants:
    @pytest.mark.parametrize("text", SAMPLE_TEXTS)
    def test_lossless(self, text: str) -> None:
        normalized = unicodedata.normalize("NFC", text)
        assert "".join(t.text for t in tokenize(text)) == normalized

    @pytest.mark.parametrize("text", SAMPLE_TEXTS)
    def test_offsets_are_contiguous_and_correct(self, text: str) -> None:
        normalized = unicodedata.normalize("NFC", text)
        tokens = tokenize(text)
        pos = 0
        for token in tokens:
            assert token.start == pos
            assert token.end == pos + len(token.text)
            assert normalized[token.start : token.end] == token.text
            pos = token.end
        assert pos == len(normalized)

    @pytest.mark.parametrize("text", SAMPLE_TEXTS)
    def test_deterministic(self, text: str) -> None:
        assert tokenize(text) == tokenize(text)


class TestVariantsSource:
    def test_variant_matches_only_when_included(self) -> None:
        from khmerthings.lexicon import load_lexicon

        text = "ព័ត៍មាន"  # common misspelling of ព័ត៌មាន
        with_variants = tokenize(text, load_lexicon("words", "variants"))
        assert [t.type for t in with_variants] == [TokenType.KHMER_WORD]
        without = tokenize(text, load_lexicon("words"))
        assert TokenType.KHMER_UNKNOWN in {t.type for t in without}
        # lossless either way
        normalized = unicodedata.normalize("NFC", text)
        assert "".join(t.text for t in with_variants) == normalized
        assert "".join(t.text for t in without) == normalized
