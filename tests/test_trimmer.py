"""Tests for batchmark.trimmer."""
from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.trimmer import (
    TrimmedBatch,
    TrimResult,
    _percentile,
    format_trim_summary,
    trim_all,
    trim_batch,
)


def make_batch(label: str, times: list[float]) -> BatchResult:
    runs = [RunResult(elapsed=t, returncode=0, stdout="", stderr="") for t in times]
    return BatchResult(label=label, runs=runs)


# --- _percentile ---

def test_percentile_min():
    assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 0) == pytest.approx(1.0)


def test_percentile_max():
    assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 100) == pytest.approx(5.0)


def test_percentile_median():
    assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50) == pytest.approx(3.0)


def test_percentile_empty_returns_zero():
    assert _percentile([], 50) == 0.0


# --- trim_batch ---

def test_trim_batch_label_preserved():
    batch = make_batch("cmd", [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    result = trim_batch(batch, lower_pct=10, upper_pct=90)
    assert result.label == "cmd"


def test_trim_batch_removes_extremes():
    times = [0.1 * i for i in range(1, 21)]  # 0.1 .. 2.0, 20 values
    batch = make_batch("x", times)
    result = trim_batch(batch, lower_pct=10, upper_pct=90)
    assert result.removed_count > 0
    assert result.total < 20


def test_trim_batch_bounds_set():
    batch = make_batch("x", [1.0, 2.0, 3.0, 4.0, 5.0])
    result = trim_batch(batch, lower_pct=0, upper_pct=100)
    assert result.lower_bound == pytest.approx(1.0)
    assert result.upper_bound == pytest.approx(5.0)


def test_trim_batch_invalid_range_raises():
    batch = make_batch("x", [1.0, 2.0])
    with pytest.raises(ValueError):
        trim_batch(batch, lower_pct=80, upper_pct=20)


def test_trim_batch_equal_percentiles_raises():
    batch = make_batch("x", [1.0, 2.0])
    with pytest.raises(ValueError):
        trim_batch(batch, lower_pct=50, upper_pct=50)


def test_trim_batch_no_removal_when_full_range():
    batch = make_batch("y", [0.5, 1.0, 1.5])
    result = trim_batch(batch, lower_pct=0, upper_pct=100)
    assert result.removed_count == 0
    assert result.total == 3


# --- trim_all ---

def test_trim_all_returns_trim_result():
    batches = [make_batch("a", [1.0, 2.0, 3.0]), make_batch("b", [0.5, 1.0, 1.5])]
    result = trim_all(batches)
    assert isinstance(result, TrimResult)
    assert len(result.batches) == 2


def test_trim_all_total_removed_aggregates():
    times = [float(i) for i in range(1, 21)]
    batches = [make_batch("a", times), make_batch("b", times)]
    result = trim_all(batches, lower_pct=10, upper_pct=90)
    assert result.total_removed == sum(b.removed_count for b in result.batches)


# --- format_trim_summary ---

def test_format_trim_summary_contains_label():
    batch = make_batch("myjob", [1.0, 2.0, 3.0])
    result = trim_all([batch], lower_pct=0, upper_pct=100)
    summary = format_trim_summary(result)
    assert "myjob" in summary


def test_format_trim_summary_contains_total_removed():
    batch = make_batch("job", [1.0, 2.0, 3.0])
    result = trim_all([batch], lower_pct=0, upper_pct=100)
    summary = format_trim_summary(result)
    assert "Total removed" in summary
