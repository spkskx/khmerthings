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

    def test_missing_subcommand_errors(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 2


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

    def test_version(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "khmerthings", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 0
        assert __version__ in proc.stdout
