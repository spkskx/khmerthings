import pytest

from khmerthings import chars
from khmerthings.chars import ScriptClass


class TestConsonants:
    @pytest.mark.parametrize(
        "ch", ["ក", "ខ", "ង", "ញ", "ដ", "ត", "ន", "ប", "ម", "យ", "រ", "ល", "ស", "ហ", "អ"]
    )
    def test_consonants(self, ch: str) -> None:
        assert chars.is_consonant(ch)

    def test_full_consonant_range(self) -> None:
        for cp in range(0x1780, 0x17A3):
            assert chars.is_consonant(chr(cp))

    @pytest.mark.parametrize("ch", ["ា", "្", "១", "k", "ឣ", "។"])
    def test_non_consonants(self, ch: str) -> None:
        assert not chars.is_consonant(ch)


class TestVowels:
    def test_independent_vowel_range(self) -> None:
        for cp in range(0x17A3, 0x17B4):
            assert chars.is_independent_vowel(chr(cp))
        assert not chars.is_independent_vowel("អ")  # U+17A2 is a consonant
        assert not chars.is_independent_vowel("ា")

    def test_dependent_vowel_range(self) -> None:
        for cp in range(0x17B6, 0x17C6):
            assert chars.is_dependent_vowel(chr(cp))
        assert not chars.is_dependent_vowel("ំ")  # U+17C6 is a sign
        assert not chars.is_dependent_vowel("ក")

    def test_inherent_vowels(self) -> None:
        assert chars.is_inherent_vowel("឴")
        assert chars.is_inherent_vowel("឵")
        assert not chars.is_inherent_vowel("ា")
        assert not chars.is_dependent_vowel("឴")


class TestSignsAndCoeng:
    @pytest.mark.parametrize("ch", ["ំ", "ះ", "៉", "៊", "់", "៌", "៍", "៎", "៏", "័", "៑", "៝"])
    def test_signs(self, ch: str) -> None:
        assert chars.is_sign(ch)

    def test_coeng(self) -> None:
        assert chars.is_coeng("្")
        assert not chars.is_sign("្")  # coeng is classified separately
        assert not chars.is_coeng("ំ")


class TestDigits:
    def test_khmer_digits(self) -> None:
        for value, cp in enumerate(range(0x17E0, 0x17EA)):
            ch = chr(cp)
            assert chars.is_khmer_digit(ch)
            assert chars.khmer_digit_to_int(ch) == value

    @pytest.mark.parametrize("ch", ["0", "9", "ក", "។"])
    def test_non_digits(self, ch: str) -> None:
        assert not chars.is_khmer_digit(ch)
        with pytest.raises(ValueError):
            chars.khmer_digit_to_int(ch)


class TestPunctuation:
    @pytest.mark.parametrize("ch", ["។", "៕", "៖", "ៗ", "៘", "៙", "៚", "ៜ"])
    def test_khmer_punctuation(self, ch: str) -> None:
        assert chars.is_khmer_punctuation(ch)

    def test_currency_sign_is_not_punctuation(self) -> None:
        assert not chars.is_khmer_punctuation("៛")

    @pytest.mark.parametrize("ch", ["ក", ".", "!", "១"])
    def test_non_khmer_punctuation(self, ch: str) -> None:
        assert not chars.is_khmer_punctuation(ch)


class TestSentenceStop:
    @pytest.mark.parametrize("ch", ["។", "៕"])
    def test_sentence_stops(self, ch: str) -> None:
        assert chars.is_khmer_sentence_stop(ch)

    @pytest.mark.parametrize("ch", ["៖", "ៗ", "ៜ", "ក", ".", "!", "១"])
    def test_non_sentence_stops(self, ch: str) -> None:
        assert not chars.is_khmer_sentence_stop(ch)


class TestBlockBoundaries:
    @pytest.mark.parametrize(
        ("ch", "expected"),
        [
            ("᝿", False),  # just before the Khmer block
            ("ក", True),  # first Khmer codepoint
            ("៿", True),  # last Khmer codepoint
            ("᠀", False),  # just after the Khmer block
            ("᧟", False),  # just before Khmer Symbols
            ("᧠", True),  # first Khmer Symbols codepoint
            ("᧿", True),  # last Khmer Symbols codepoint
            ("ᨀ", False),  # just after Khmer Symbols
            ("a", False),
            ("1", False),
        ],
    )
    def test_is_khmer(self, ch: str, expected: bool) -> None:
        assert chars.is_khmer(ch) is expected


class TestScriptClass:
    @pytest.mark.parametrize(
        ("ch", "expected"),
        [
            ("ក", ScriptClass.KHMER),
            ("ា", ScriptClass.KHMER),
            ("១", ScriptClass.KHMER),
            ("។", ScriptClass.KHMER),
            ("a", ScriptClass.LATIN),
            ("Z", ScriptClass.LATIN),
            ("5", ScriptClass.DIGIT),
            (" ", ScriptClass.OTHER),
            ("é", ScriptClass.OTHER),  # non-ASCII Latin is OTHER by design
            ("!", ScriptClass.OTHER),
        ],
    )
    def test_script_class(self, ch: str, expected: ScriptClass) -> None:
        assert chars.script_class(ch) is expected


class TestKhmerLetterOrMark:
    @pytest.mark.parametrize("ch", ["ក", "ឣ", "ា", "ំ", "្", "឴"])
    def test_letters_and_marks(self, ch: str) -> None:
        assert chars.is_khmer_letter_or_mark(ch)

    @pytest.mark.parametrize("ch", ["១", "។", "៛", "a", " "])
    def test_non_letters(self, ch: str) -> None:
        assert not chars.is_khmer_letter_or_mark(ch)


class TestSingleCharacterContract:
    @pytest.mark.parametrize("bad", ["", "កា"])
    def test_multi_char_raises(self, bad: str) -> None:
        with pytest.raises(ValueError):
            chars.is_khmer(bad)
