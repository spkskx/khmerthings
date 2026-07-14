import json
import subprocess
import sys
from pathlib import Path

import pytest

from khmerthings import __version__
from khmerthings.cli import main

SENTENCE = "ខ្ញុំស្រឡាញ់ភាសាខ្មែរ"  # 4 words


class TestMain:
    def test_count_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "sample.txt"
        f.write_text(SENTENCE, encoding="utf-8")
        assert main(["count", str(f)]) == 0
        out = capsys.readouterr().out
        assert "total_words: 4" in out
        assert "khmer_words: 4" in out

    def test_count_json(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "sample.txt"
        f.write_text(SENTENCE, encoding="utf-8")
        assert main(["count", "--json", str(f)]) == 0
        data = json.loads(capsys.readouterr().out)
        assert data == [
            {
                "source": str(f),
                "total_words": 4,
                "khmer_words": 4,
                "unknown_khmer_words": 0,
                "latin_words": 0,
                "numbers": 0,
                "clusters": 8,
                "khmer_characters": 21,
                "characters": 21,
            }
        ]

    def test_multiple_files_are_labelled(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("ខ្ញុំ", encoding="utf-8")
        b.write_text("hello world", encoding="utf-8")
        assert main(["count", str(a), str(b)]) == 0
        out = capsys.readouterr().out
        assert f"{a}:" in out
        assert f"{b}:" in out

    def test_segment_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ខ្ញុំស្រឡាញ់ភាសាខ្មែរ\n", encoding="utf-8")
        assert main(["segment", str(f)]) == 0
        assert capsys.readouterr().out == "ខ្ញុំ ស្រឡាញ់ ភាសា ខ្មែរ\n"

    def test_segment_custom_separator(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ខ្ញុំទៅផ្សារ\n", encoding="utf-8")
        assert main(["segment", "--separator", "|", str(f)]) == 0
        assert capsys.readouterr().out == "ខ្ញុំ|ទៅ|ផ្សារ\n"

    def test_segment_mark_mode_defaults_to_zwsp(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ខ្ញុំទៅ ផ្សារ។\n", encoding="utf-8")
        assert main(["segment", "--mark", str(f)]) == 0
        assert capsys.readouterr().out == "ខ្ញុំ​ទៅ ផ្សារ។\n"

    def test_segment_mark_mode_custom_separator(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ខ្ញុំទៅផ្សារ\n", encoding="utf-8")
        assert main(["segment", "--mark", "--separator", "/", str(f)]) == 0
        assert capsys.readouterr().out == "ខ្ញុំ/ទៅ/ផ្សារ\n"

    def test_segment_include_names(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        # Two adjacent given names, both only in the names wordlist.
        f.write_text("សុខាដារ៉ា\n", encoding="utf-8")
        assert main(["segment", str(f)]) == 0
        assert capsys.readouterr().out == "សុខាដារ៉ា\n"  # one unknown span without names
        assert main(["segment", "--include", "names", str(f)]) == 0
        assert capsys.readouterr().out == "សុខា ដារ៉ា\n"

    def test_count_include_modern(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "text.txt"
        # ឡូយ (slang) + ហ្វេសប៊ុក (loanword) are only in the modern wordlist.
        f.write_text("ហ្វេសប៊ុកឡូយណាស់", encoding="utf-8")
        assert main(["count", "--include", "modern", str(f)]) == 0
        out = capsys.readouterr().out
        assert "khmer_words: 3" in out
        assert "unknown_khmer_words: 0" in out

    def test_include_unknown_source_errors(self, tmp_path: Path) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ខ្ញុំ", encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            main(["count", "--include", "bogus", str(f)])
        assert exc.value.code == 2

    def test_sort_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "lines.txt"
        f.write_text("ខ\nក\nគ\n", encoding="utf-8")
        assert main(["sort", str(f)]) == 0
        assert capsys.readouterr().out == "ក\nខ\nគ\n"

    def test_sort_descending(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "lines.txt"
        f.write_text("ក\nគ\nខ\n", encoding="utf-8")
        assert main(["sort", "--desc", str(f)]) == 0
        assert capsys.readouterr().out == "គ\nខ\nក\n"

    def test_sort_merges_multiple_files(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("គ\nក\n", encoding="utf-8")
        b.write_text("ខ\n", encoding="utf-8")
        assert main(["sort", str(a), str(b)]) == 0
        assert capsys.readouterr().out == "ក\nខ\nគ\n"

    def test_spellcheck_clean_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text(SENTENCE + "\n", encoding="utf-8")
        assert main(["spellcheck", str(f)]) == 0
        assert capsys.readouterr().out == ""

    def test_spellcheck_reports_variant(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ខ្ញុំសំរាប់ការងារ\n", encoding="utf-8")
        assert main(["spellcheck", str(f)]) == 1
        assert capsys.readouterr().out == f"{f}:1:6: variant: សំរាប់ -> សម្រាប់\n"

    def test_spellcheck_json(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "text.txt"
        f.write_text("សំរាប់\n", encoding="utf-8")
        assert main(["spellcheck", "--json", str(f)]) == 1
        data = json.loads(capsys.readouterr().out)
        assert data == [
            {
                "source": str(f),
                "line": 1,
                "col": 1,
                "start": 0,
                "end": 6,
                "text": "សំរាប់",
                "kind": "variant",
                "suggestions": ["សម្រាប់"],
            }
        ]

    def test_spellcheck_json_clean_is_empty_list(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text(SENTENCE, encoding="utf-8")
        assert main(["spellcheck", "--json", str(f)]) == 0
        assert json.loads(capsys.readouterr().out) == []

    def test_spellcheck_max_suggestions(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ស្រឡាញ\n", encoding="utf-8")  # unknown, near ស្រឡាញ់
        assert main(["spellcheck", "--max-suggestions", "0", str(f)]) == 1
        assert capsys.readouterr().out == f"{f}:1:1: unknown: ស្រឡាញ\n"

    def test_spellcheck_include_names(self, tmp_path: Path) -> None:
        f = tmp_path / "text.txt"
        f.write_text("សុខា\n", encoding="utf-8")  # given name, only in names list
        assert main(["spellcheck", str(f)]) == 1
        assert main(["spellcheck", "--include", "names", str(f)]) == 0

    def test_spellfix_rewrites_variants(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ខ្ញុំសំរាប់ការងារ\nសំរាប់ កំរិត\n", encoding="utf-8")
        assert main(["spellfix", str(f)]) == 0
        assert capsys.readouterr().out == "ខ្ញុំសម្រាប់ការងារ\nសម្រាប់ កម្រិត\n"

    def test_spellfix_clean_text_unchanged(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text(SENTENCE + "\n", encoding="utf-8")
        assert main(["spellfix", str(f)]) == 0
        assert capsys.readouterr().out == SENTENCE + "\n"

    def test_condense_default(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ខ្ញុំចង់ទៅផ្សារនៅ\n", encoding="utf-8")
        assert main(["condense", str(f)]) == 0
        assert capsys.readouterr().out == "ខ្ញុំ​ចង់​ទៅ​ផ្សារ\n"

    def test_condense_words_flag(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ខ្ញុំចង់ទៅផ្សារនៅ\n", encoding="utf-8")
        assert main(["condense", "--words", str(f)]) == 0
        assert capsys.readouterr().out == "ខ្ញុំ\nចង់\nទៅ\nផ្សារ\n"

    def test_condense_remove_categories(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ខ្ញុំចង់ទៅផ្សារនៅ\n", encoding="utf-8")
        assert main(["condense", "--remove", "preposition,pronoun,auxiliary", str(f)]) == 0
        assert capsys.readouterr().out == "ទៅ​ផ្សារ\n"

    def test_romanize_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ភ្នំពេញ\n", encoding="utf-8")
        assert main(["romanize", str(f)]) == 0
        assert capsys.readouterr().out == "phnom penh\n"

    def test_romanize_digits_and_passthrough(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text("hello ២០២៦\n", encoding="utf-8")
        assert main(["romanize", str(f)]) == 0
        assert capsys.readouterr().out == "hello 2026\n"

    def test_numerals_to_khmer(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "text.txt"
        f.write_text("42\n", encoding="utf-8")
        assert main(["numerals", "--to", "khmer", str(f)]) == 0
        assert capsys.readouterr().out == "៤២\n"

    def test_numerals_to_arabic(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "text.txt"
        f.write_text("១២៣ and 456\n", encoding="utf-8")
        assert main(["numerals", "--to", "arabic", str(f)]) == 0
        assert capsys.readouterr().out == "123 and 456\n"

    def test_numerals_to_words(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "text.txt"
        f.write_text("លេខ 25 នៅ\n", encoding="utf-8")
        assert main(["numerals", "--to", "words", str(f)]) == 0
        assert capsys.readouterr().out == "លេខ ម្ភៃប្រាំ នៅ\n"

    def test_validate_reports_issue_and_exit_one(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ក្ឥ\n", encoding="utf-8")
        assert main(["validate", str(f)]) == 1
        assert capsys.readouterr().out == f"{f}:1:2: invalid_coeng_follower: ្ឥ\n"

    def test_validate_json_clean_and_invalid(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text("ក\nកាិ\n", encoding="utf-8")
        assert main(["validate", "--json", str(f)]) == 1
        assert json.loads(capsys.readouterr().out) == [
            {
                "source": str(f),
                "line": 2,
                "col": 3,
                "start": 2,
                "end": 3,
                "text": "ិ",
                "code": "repeated_dependent_vowel",
            }
        ]

    def test_numerals_default_is_khmer(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "text.txt"
        f.write_text("2026\n", encoding="utf-8")
        assert main(["numerals", str(f)]) == 0
        assert capsys.readouterr().out == "២០២៦\n"

    def test_missing_file_is_a_clean_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["count", "/nonexistent/path.txt"]) == 1
        err = capsys.readouterr().err
        assert err.startswith("khmerthings: error:")

    def test_missing_subcommand_errors(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 2


SUBCOMMANDS = [
    "count",
    "segment",
    "sort",
    "spellcheck",
    "spellfix",
    "normalize",
    "condense",
    "romanize",
    "numerals",
    "validate",
]


class TestInputParity:
    """Every subcommand survives empty and non-Khmer input without crashing.

    A degenerate input must exit 0 (success) — never raise, never error out.
    ``spellcheck`` uses exit 1 only for *issues found*; empty/non-Khmer text
    has none, so it too must be 0.
    """

    @pytest.mark.parametrize("sub", SUBCOMMANDS)
    @pytest.mark.parametrize("content", ["", "\n", "hello world 123 !@#\n", "   "])
    def test_degenerate_input_exits_zero(
        self, sub: str, content: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "in.txt"
        f.write_text(content, encoding="utf-8")
        assert main([sub, str(f)]) == 0
        capsys.readouterr()  # drain

    @pytest.mark.parametrize("sub", SUBCOMMANDS)
    def test_missing_file_is_clean_error_for_every_subcommand(
        self, sub: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main([sub, "/nonexistent/path.txt"]) == 1
        assert capsys.readouterr().err.startswith("khmerthings: error:")


class TestSubprocess:
    def test_stdin(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "khmerthings", "count", "-"],
            input=SENTENCE,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 0
        assert "total_words: 4" in proc.stdout

    def test_stdin_is_default(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "khmerthings", "count"],
            input="hello ខ្ញុំ",
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 0
        assert "total_words: 2" in proc.stdout

    def test_segment_stdin(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "khmerthings", "segment", "-"],
            input="ខ្ញុំស្រឡាញ់ភាសាខ្មែរ\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 0
        assert proc.stdout == "ខ្ញុំ ស្រឡាញ់ ភាសា ខ្មែរ\n"

    def test_sort_stdin(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "khmerthings", "sort", "-"],
            input="ខ្ញុំ\nកា\nក្រ\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 0
        assert proc.stdout == "កា\nក្រ\nខ្ញុំ\n"

    def test_spellcheck_stdin_exit_code(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "khmerthings", "spellcheck"],
            input="សំរាប់\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 1
        assert "សម្រាប់" in proc.stdout

    def test_spellfix_stdin(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "khmerthings", "spellfix"],
            input="សំរាប់\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 0
        assert proc.stdout == "សម្រាប់\n"

    def test_romanize_stdin(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "khmerthings", "romanize"],
            input="ភ្នំពេញ\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 0
        assert proc.stdout == "phnom penh\n"

    def test_numerals_stdin(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "khmerthings", "numerals", "--to", "words"],
            input="7\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 0
        assert proc.stdout == "ប្រាំពីរ\n"

    def test_version(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "khmerthings", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 0
        assert __version__ in proc.stdout
