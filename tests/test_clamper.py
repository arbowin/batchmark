"""Tests for batchmark.clamper."""
from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.clamper import (
    ClampedBatch,
    ClampResult,
    clamp_batch,
    clamp_all,
    format_clamp_summary,
)


def make_batch(label: str, elapsed_values: list[float]) -> BatchResult:
    runs = [
        RunResult(command="echo", elapsed=e, returncode=0, stdout="", stderr="")
        for e in elapsed_values
    ]
    return BatchResult(label=label, runs=runs)


# --- clamp_batch ---

def test_clamp_batch_no_runs_outside_range():
    batch = make_batch("cmd", [10.0, 20.0, 30.0])
    result = clamp_batch(batch, min_ms=5.0, max_ms=50.0)
    assert result.clamped_count == 0
    assert [r.elapsed for r in result.runs] == [10.0, 20.0, 30.0]


def test_clamp_batch_all_above_max():
    batch = make_batch("cmd", [100.0, 200.0, 300.0])
    result = clamp_batch(batch, max_ms=50.0)
    assert result.clamped_count == 3
    assert all(r.elapsed == 50.0 for r in result.runs)


def test_clamp_batch_all_below_min():
    batch = make_batch("cmd", [1.0, 2.0, 3.0])
    result = clamp_batch(batch, min_ms=10.0)
    assert result.clamped_count == 3
    assert all(r.elapsed == 10.0 for r in result.runs)


def test_clamp_batch_partial_clamping():
    batch = make_batch("cmd", [1.0, 50.0, 200.0])
    result = clamp_batch(batch, min_ms=5.0, max_ms=100.0)
    assert result.clamped_count == 2
    assert result.runs[0].elapsed == 5.0
    assert result.runs[1].elapsed == 50.0
    assert result.runs[2].elapsed == 100.0


def test_clamp_batch_preserves_returncode():
    runs = [
        RunResult(command="x", elapsed=999.0, returncode=1, stdout="", stderr="err")
    ]
    batch = BatchResult(label="fail", runs=runs)
    result = clamp_batch(batch, max_ms=10.0)
    assert result.runs[0].returncode == 1
    assert result.runs[0].stderr == "err"


def test_clamp_batch_label_preserved():
    batch = make_batch("my-label", [5.0])
    result = clamp_batch(batch, max_ms=100.0)
    assert result.label == "my-label"


def test_clamp_batch_invalid_range_raises():
    batch = make_batch("cmd", [10.0])
    with pytest.raises(ValueError, match="min_ms"):
        clamp_batch(batch, min_ms=50.0, max_ms=10.0)


def test_clamp_batch_only_min():
    batch = make_batch("cmd", [0.5, 10.0])
    result = clamp_batch(batch, min_ms=1.0)
    assert result.clamped_count == 1
    assert result.runs[0].elapsed == 1.0
    assert result.runs[1].elapsed == 10.0


# --- clamp_all ---

def test_clamp_all_returns_clamp_result():
    batches = [make_batch("a", [1.0, 200.0]), make_batch("b", [5.0, 50.0])]
    result = clamp_all(batches, min_ms=2.0, max_ms=100.0)
    assert isinstance(result, ClampResult)
    assert len(result.batches) == 2


def test_clamp_all_total_clamped():
    batches = [make_batch("a", [1.0, 200.0]), make_batch("b", [0.5, 50.0])]
    result = clamp_all(batches, min_ms=2.0, max_ms=100.0)
    assert result.total_clamped == 3  # 1.0->2.0, 200->100, 0.5->2.0


# --- format_clamp_summary ---

def test_format_clamp_summary_contains_header():
    batches = [make_batch("cmd", [10.0])]
    result = clamp_all(batches, max_ms=50.0)
    text = format_clamp_summary(result)
    assert "Clamp summary" in text


def test_format_clamp_summary_contains_label():
    batches = [make_batch("my-cmd", [10.0, 200.0])]
    result = clamp_all(batches, max_ms=50.0)
    text = format_clamp_summary(result)
    assert "my-cmd" in text


def test_format_clamp_summary_shows_total():
    batches = [make_batch("a", [1.0, 200.0]), make_batch("b", [300.0])]
    result = clamp_all(batches, max_ms=100.0)
    text = format_clamp_summary(result)
    assert "3" in text  # total_clamped
