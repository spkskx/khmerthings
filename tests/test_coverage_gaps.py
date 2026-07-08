"""Tests for the dev-only coverage-gap harness (``scripts/coverage_gaps.py``)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "coverage_gaps.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("coverage_gaps", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


coverage_gaps = _load()


class TestCollectGaps:
    def test_all_known_text_has_no_gaps(self) -> None:
        unknown, khmer_words = coverage_gaps.collect_gaps("ខ្ញុំទៅផ្សារ")
        assert unknown == {}
        assert khmer_words > 0

    def test_unknown_span_is_reported_and_counted(self) -> None:
        # A clearly-invented cluster run must surface as an unknown span.
        unknown, khmer_words = coverage_gaps.collect_gaps("ខ្ញុំក្ស្ក្ស")
        assert khmer_words >= 1
        assert unknown  # at least one unknown span
        # every reported span is non-empty Khmer text
        assert all(span for span in unknown)

    def test_repeated_gap_accumulates_count(self) -> None:
        # Same unknown span twice → count of 2.
        unknown, _ = coverage_gaps.collect_gaps("ក្ស្ក ក្ស្ក")
        assert unknown.most_common(1)[0][1] == 2

    def test_empty_text(self) -> None:
        unknown, khmer_words = coverage_gaps.collect_gaps("")
        assert unknown == {}
        assert khmer_words == 0


class TestFormatReport:
    def test_reports_coverage_and_threshold(self) -> None:
        from collections import Counter

        report = coverage_gaps.format_report(Counter({"ក្ស្ក": 3, "ខ្ស": 1}), 10, min_count=2)
        assert "coverage" in report
        assert "ក្ស្ក" in report  # count 3 ≥ 2
        assert "ខ្ស" not in report  # count 1 < threshold

    def test_no_gaps_message(self) -> None:
        from collections import Counter

        report = coverage_gaps.format_report(Counter(), 5, min_count=1)
        assert "coverage 100.0%" in report


class TestMain:
    def test_reads_stdin(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        import io

        monkeypatch.setattr("sys.stdin", io.StringIO("ខ្ញុំទៅ"))
        assert coverage_gaps.main([]) == 0
        assert "coverage" in capsys.readouterr().out
