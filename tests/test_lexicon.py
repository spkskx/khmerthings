import pytest

from khmerthings.clusters import segment_clusters
from khmerthings.clusters import segment_clusters as segment_clusters_for_match
from khmerthings.lexicon import (
    WORD_SOURCES,
    Lexicon,
    default_lexicon,
    load_lexicon,
    load_variants,
    parse_variants,
)


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


class TestLoadLexicon:
    def test_no_args_loads_core_words(self) -> None:
        assert load_lexicon() is load_lexicon("words")
        assert default_lexicon() is load_lexicon("words")

    def test_caching_per_combination(self) -> None:
        assert load_lexicon("words", "names") is load_lexicon("words", "names")

    @pytest.mark.parametrize("source", sorted(WORD_SOURCES))
    def test_each_source_loads_and_validates(self, source: str) -> None:
        lex = load_lexicon(source)
        assert len(lex) > 0
        Lexicon(list(lex))  # every entry re-validates

    def test_names_source(self) -> None:
        names = load_lexicon("names")
        for entry in ["សុខា", "ហ៊ុន", "ឯកឧត្តម", "បុប្ផា", "ដារ៉ា"]:
            assert entry in names
        assert "ខ្ញុំ" not in names  # core vocabulary lives in words.txt

    def test_modern_source(self) -> None:
        modern = load_lexicon("modern")
        for entry in ["ឡូយ", "ស្ទាវ", "ហ្វេសប៊ុក", "អនឡាញ", "កូវីដ"]:
            assert entry in modern
        assert "ខ្ញុំ" not in modern

    def test_merge_deduplicates_across_files(self) -> None:
        # ខៀវ is both a color (words) and a surname (names).
        assert "ខៀវ" in load_lexicon("words")
        assert "ខៀវ" in load_lexicon("names")
        merged = load_lexicon("words", "names", "modern")
        assert len(merged) < len(load_lexicon("words")) + len(load_lexicon("names")) + len(
            load_lexicon("modern")
        )
        assert len(merged) >= len(load_lexicon("words"))

    def test_merged_lexicon_matches_names(self) -> None:
        merged = load_lexicon("words", "names")
        assert merged.longest_match(segment_clusters_for_match("សុខា")) == 2  # សុ ខា

    def test_unknown_source_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown word source"):
            load_lexicon("words", "nope")


class TestParseVariants:
    def test_basic_mapping(self) -> None:
        mapping = parse_variants(["# comment", "", "ព័ត៍មាន\tព័ត៌មាន", "  អោយ\tឱ្យ  "])
        assert mapping == {"ព័ត៍មាន": "ព័ត៌មាន", "អោយ": "ឱ្យ"}

    @pytest.mark.parametrize(
        ("line", "match"),
        [
            ("ព័ត៍មាន", "malformed"),  # no tab
            ("ព័ត៍មាន\t", "malformed"),  # empty canonical
            ("\tព័ត៌មាន", "malformed"),  # empty variant
            ("hello\tព័ត៌មាន", "non-Khmer"),
            ("ព័ត៍មាន\tnews", "non-Khmer"),
            ("ព័ត៌មាន\tព័ត៌មាន", "maps to itself"),
        ],
    )
    def test_bad_lines_rejected(self, line: str, match: str) -> None:
        with pytest.raises(ValueError, match=match):
            parse_variants([line])

    def test_duplicate_variant_rejected(self) -> None:
        with pytest.raises(ValueError, match="duplicate variant"):
            parse_variants(["អោយ\tឱ្យ", "អោយ\tឲ្យ"])

    def test_chained_variant_rejected(self) -> None:
        # a canonical target may not itself be listed as a variant
        with pytest.raises(ValueError, match="itself listed as a variant"):
            parse_variants(["ពត៌មាន\tព័ត៍មាន", "ព័ត៍មាន\tព័ត៌មាន"])


class TestLoadVariants:
    def test_loads_and_is_cached(self) -> None:
        variants = load_variants()
        assert variants is load_variants()
        assert variants["ព័ត៍មាន"] == "ព័ត៌មាន"
        assert variants["អោយ"] == "ឱ្យ"

    def test_every_canonical_is_a_canonical_entry(self) -> None:
        merged = load_lexicon("words", "names", "modern")
        for variant, canonical in load_variants().items():
            assert canonical in merged, f"{variant!r} -> {canonical!r} not in canonical sources"

    def test_no_variant_is_a_canonical_entry(self) -> None:
        # a spelling cannot be both a misspelling and a real word/name
        merged = load_lexicon("words", "names", "modern")
        for variant in load_variants():
            assert variant not in merged, f"{variant!r} is both variant and canonical"

    def test_variants_source_contributes_misspellings(self) -> None:
        lex = load_lexicon("words", "variants")
        assert "ព័ត៍មាន" in lex  # variant matches
        assert "ព័ត៌មាន" in lex  # canonical still matches
        assert "ព័ត៍មាន" not in load_lexicon("words")
