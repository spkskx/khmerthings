import pytest

from khmerthings.clusters import segment_clusters
from khmerthings.lexicon import Lexicon, default_lexicon


class TestConstruction:
    def test_basic(self) -> None:
        lex = Lexicon(["ខ្ញុំ", "ទៅ"])
        assert len(lex) == 2
        assert "ខ្ញុំ" in lex
        assert "ទៅ" in lex
        assert "ភាសា" not in lex

    def test_iteration_is_sorted(self) -> None:
        lex = Lexicon(["ទៅ", "ខ្ញុំ"])
        assert list(lex) == sorted(["ទៅ", "ខ្ញុំ"])

    def test_empty_word_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            Lexicon([""])

    def test_duplicate_rejected(self) -> None:
        with pytest.raises(ValueError, match="duplicate"):
            Lexicon(["ខ្ញុំ", "ខ្ញុំ"])

    @pytest.mark.parametrize("bad", ["hello", "កា x", "ខ្ញុំ១", "ការ។"])
    def test_non_khmer_letters_rejected(self, bad: str) -> None:
        with pytest.raises(ValueError, match="non-Khmer"):
            Lexicon([bad])


class TestFromLines:
    def test_skips_comments_and_blanks(self) -> None:
        lines = ["# comment", "", "ខ្ញុំ", "  ", "ទៅ  ", "​ភាសា​"]
        lex = Lexicon.from_lines(lines)
        assert len(lex) == 3
        assert "ភាសា" in lex


class TestLongestMatch:
    def test_no_match(self) -> None:
        lex = Lexicon(["ខ្ញុំ"])
        assert lex.longest_match(segment_clusters("ភាសា")) == 0

    def test_simple_match(self) -> None:
        lex = Lexicon(["ភាសា"])
        assert lex.longest_match(segment_clusters("ភាសា")) == 2

    def test_prefers_longest(self) -> None:
        # កា is a prefix (in clusters) of ការ and ការងារ
        lex = Lexicon(["កា", "ការ", "ការងារ"])
        clusters = segment_clusters("ការងារ")  # កា រ ងា រ
        assert lex.longest_match(clusters) == 4

    def test_falls_back_to_shorter_word(self) -> None:
        lex = Lexicon(["កា", "ការងារ"])
        clusters = segment_clusters("ការទៅ")  # កា រ ទៅ — ការងារ doesn't match
        assert lex.longest_match(clusters) == 1  # matches កា only

    def test_start_offset(self) -> None:
        lex = Lexicon(["ភាសា"])
        clusters = segment_clusters("ខ្ញុំភាសា")  # ខ្ញុំ ភា សា
        assert lex.longest_match(clusters, start=0) == 0
        assert lex.longest_match(clusters, start=1) == 2

    def test_match_cannot_split_clusters(self) -> None:
        # ខ្ញ is not a full cluster of ខ្ញុំ, so it must never match.
        lex = Lexicon(["ខ្ញុំ"])
        assert lex.longest_match(segment_clusters("ខ្ញា")) == 0

    def test_empty_input(self) -> None:
        lex = Lexicon(["ខ្ញុំ"])
        assert lex.longest_match([]) == 0


class TestDefaultLexicon:
    def test_loads_and_is_cached(self) -> None:
        lex = default_lexicon()
        assert lex is default_lexicon()
        assert len(lex) > 200

    @pytest.mark.parametrize("word", ["ខ្ញុំ", "ស្រឡាញ់", "ភាសា", "ខ្មែរ", "អរគុណ", "កម្ពុជា"])
    def test_contains_core_words(self, word: str) -> None:
        assert word in default_lexicon()

    def test_all_entries_valid(self) -> None:
        # Re-validating via the constructor exercises every entry.
        Lexicon(list(default_lexicon()))
