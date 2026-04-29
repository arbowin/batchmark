"""Tests for batchmark.pivotter."""
from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.pivotter import (
    PivotCell,
    PivotResult,
    _compute_metric,
    pivot,
    format_pivot,
    _METRICS,
)


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times, rcs=None) -> BatchResult:
    if rcs is None:
        rcs = [0] * len(times)
    return BatchResult(label=label, runs=[_run(t, r) for t, r in zip(times, rcs)])


def test_compute_metric_mean():
    b = make_batch("a", [1.0, 3.0])
    assert _compute_metric(b, "mean") == pytest.approx(2.0)


def test_compute_metric_median():
    b = make_batch("a", [1.0, 2.0, 3.0])
    assert _compute_metric(b, "median") == pytest.approx(2.0)


def test_compute_metric_min_max():
    b = make_batch("a", [1.0, 5.0, 3.0])
    assert _compute_metric(b, "min") == pytest.approx(1.0)
    assert _compute_metric(b, "max") == pytest.approx(5.0)


def test_compute_metric_success_rate_full():
    b = make_batch("a", [1.0, 2.0], rcs=[0, 0])
    assert _compute_metric(b, "success_rate") == pytest.approx(1.0)


def test_compute_metric_success_rate_partial():
    b = make_batch("a", [1.0, 2.0], rcs=[0, 1])
    assert _compute_metric(b, "success_rate") == pytest.approx(0.5)


def test_compute_metric_empty_returns_zero():
    b = BatchResult(label="empty", runs=[])
    assert _compute_metric(b, "mean") == 0.0
    assert _compute_metric(b, "success_rate") == 0.0


def test_compute_metric_unknown_raises():
    b = make_batch("a", [1.0])
    with pytest.raises(ValueError, match="Unknown metric"):
        _compute_metric(b, "bogus")


def test_pivot_empty_raises():
    with pytest.raises(ValueError, match="at least one"):
        pivot([])


def test_pivot_unknown_metric_raises():
    b = make_batch("a", [1.0])
    with pytest.raises(ValueError, match="Unknown metric"):
        pivot([b], metrics=["bogus"])


def test_pivot_labels_match_batches():
    b1 = make_batch("cmd-a", [1.0, 2.0])
    b2 = make_batch("cmd-b", [3.0, 4.0])
    result = pivot([b1, b2], metrics=["mean"])
    assert result.labels == ["cmd-a", "cmd-b"]


def test_pivot_metrics_stored():
    b = make_batch("x", [1.0])
    result = pivot([b], metrics=["mean", "min"])
    assert result.metrics == ["mean", "min"]


def test_pivot_cell_values_correct():
    b = make_batch("x", [2.0, 4.0])
    result = pivot([b], metrics=["mean", "max"])
    assert result.get("x", "mean") == pytest.approx(3.0)
    assert result.get("x", "max") == pytest.approx(4.0)


def test_pivot_get_missing_returns_none():
    b = make_batch("x", [1.0])
    result = pivot([b], metrics=["mean"])
    assert result.get("y", "mean") is None
    assert result.get("x", "min") is None


def test_pivot_default_metrics_all():
    b = make_batch("x", [1.0])
    result = pivot([b])
    assert set(result.metrics) == set(_METRICS)


def test_format_pivot_contains_label():
    b = make_batch("my-cmd", [1.0, 2.0])
    result = pivot([b], metrics=["mean"])
    text = format_pivot(result)
    assert "my-cmd" in text


def test_format_pivot_contains_metric_header():
    b = make_batch("x", [1.0])
    result = pivot([b], metrics=["mean", "stdev"])
    text = format_pivot(result)
    assert "mean" in text
    assert "stdev" in text


def test_format_pivot_multiple_rows():
    b1 = make_batch("fast", [0.1, 0.2])
    b2 = make_batch("slow", [1.0, 2.0])
    result = pivot([b1, b2], metrics=["mean"])
    text = format_pivot(result)
    assert "fast" in text
    assert "slow" in text
