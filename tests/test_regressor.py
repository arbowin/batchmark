"""Tests for batchmark.regressor."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.regressor import (
    RegressionEntry,
    RegressionReport,
    detect_regressions,
    format_regression_report,
)


def _run(elapsed: float, ok: bool = True) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=0 if ok else 1)


def _batch(label: str, *times: float) -> BatchResult:
    return BatchResult(label=label, runs=[_run(t) for t in times])


# ---------------------------------------------------------------------------
# detect_regressions
# ---------------------------------------------------------------------------

def test_detect_returns_entry_for_common_labels():
    baseline = {"cmd_a": 1.0, "cmd_b": 2.0}
    current = [_batch("cmd_a", 1.0, 1.2), _batch("cmd_b", 2.0)]
    report = detect_regressions(baseline, current)
    labels = {e.label for e in report.entries}
    assert "cmd_a" in labels
    assert "cmd_b" in labels


def test_detect_ignores_labels_not_in_baseline():
    baseline = {"cmd_a": 1.0}
    current = [_batch("cmd_a", 1.0), _batch("cmd_z", 0.5)]
    report = detect_regressions(baseline, current)
    labels = {e.label for e in report.entries}
    assert "cmd_z" not in labels


def test_detect_ignores_labels_not_in_current():
    baseline = {"cmd_a": 1.0, "cmd_missing": 0.5}
    current = [_batch("cmd_a", 1.0)]
    report = detect_regressions(baseline, current)
    labels = {e.label for e in report.entries}
    assert "cmd_missing" not in labels


def test_detect_regression_verdict():
    baseline = {"slow": 1.0}
    current = [_batch("slow", 1.2)]   # +20 % > default 5 %
    report = detect_regressions(baseline, current)
    assert report.entries[0].verdict == "regressed"


def test_detect_improvement_verdict():
    baseline = {"fast": 1.0}
    current = [_batch("fast", 0.8)]   # -20 %
    report = detect_regressions(baseline, current)
    assert report.entries[0].verdict == "improved"


def test_detect_stable_verdict():
    baseline = {"steady": 1.0}
    current = [_batch("steady", 1.02)]  # +2 % < 5 %
    report = detect_regressions(baseline, current)
    assert report.entries[0].verdict == "stable"


def test_detect_custom_threshold():
    baseline = {"cmd": 1.0}
    current = [_batch("cmd", 1.03)]   # +3 % — regressed at 2 %, stable at 5 %
    report_strict = detect_regressions(baseline, current, threshold_pct=2.0)
    report_loose = detect_regressions(baseline, current, threshold_pct=5.0)
    assert report_strict.entries[0].verdict == "regressed"
    assert report_loose.entries[0].verdict == "stable"


def test_detect_negative_threshold_raises():
    with pytest.raises(ValueError):
        detect_regressions({"x": 1.0}, [], threshold_pct=-1.0)


def test_detect_delta_pct_calculation():
    baseline = {"cmd": 2.0}
    current = [_batch("cmd", 2.5)]
    report = detect_regressions(baseline, current)
    entry = report.entries[0]
    assert abs(entry.delta_pct - 25.0) < 1e-6


# ---------------------------------------------------------------------------
# RegressionReport helpers
# ---------------------------------------------------------------------------

def test_report_regressions_filter():
    entries = [
        RegressionEntry("a", 1.0, 1.2, 0.2, 20.0, "regressed"),
        RegressionEntry("b", 1.0, 0.8, -0.2, -20.0, "improved"),
        RegressionEntry("c", 1.0, 1.01, 0.01, 1.0, "stable"),
    ]
    report = RegressionReport(entries=entries)
    assert len(report.regressions()) == 1
    assert len(report.improvements()) == 1
    assert len(report.stable()) == 1


# ---------------------------------------------------------------------------
# format_regression_report
# ---------------------------------------------------------------------------

def test_format_empty_report():
    report = RegressionReport(entries=[])
    text = format_regression_report(report)
    assert "No common labels" in text


def test_format_contains_label():
    baseline = {"my_cmd": 1.0}
    current = [_batch("my_cmd", 1.0)]
    report = detect_regressions(baseline, current)
    text = format_regression_report(report)
    assert "my_cmd" in text


def test_format_contains_verdict():
    baseline = {"cmd": 1.0}
    current = [_batch("cmd", 2.0)]
    report = detect_regressions(baseline, current)
    text = format_regression_report(report)
    assert "regressed" in text
