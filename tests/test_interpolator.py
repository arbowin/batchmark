"""Tests for batchmark.interpolator."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.interpolator import (
    _linear_fill,
    interpolate_batch,
    interpolate,
    format_interpolate_summary,
    InterpolatedBatch,
    InterpolateResult,
)


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(command="echo", elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times) -> BatchResult:
    return BatchResult(label=label, runs=[_run(t) for t in times])


# --- _linear_fill ---

def test_linear_fill_no_change_when_already_target():
    result = _linear_fill([1.0, 2.0, 3.0], 3)
    assert result == [1.0, 2.0, 3.0]


def test_linear_fill_expands_to_target():
    result = _linear_fill([0.0, 4.0], 3)
    assert len(result) == 3
    assert result[0] == 0.0
    assert result[-1] == 4.0


def test_linear_fill_midpoint_is_average():
    result = _linear_fill([0.0, 2.0], 3)
    assert result[1] == pytest.approx(1.0)


def test_linear_fill_empty_returns_empty():
    assert _linear_fill([], 5) == []


def test_linear_fill_single_element_returns_single():
    assert _linear_fill([3.0], 1) == [3.0]


# --- interpolate_batch ---

def test_interpolate_batch_no_change_when_at_target():
    batch = make_batch("cmd", [1.0, 2.0, 3.0])
    ib = interpolate_batch(batch, 3)
    assert ib.added_count == 0
    assert ib.total == 3


def test_interpolate_batch_expands_runs():
    batch = make_batch("cmd", [0.0, 4.0])
    ib = interpolate_batch(batch, 4)
    assert ib.total == 4
    assert ib.added_count == 2


def test_interpolate_batch_label_preserved():
    batch = make_batch("my-label", [1.0, 2.0])
    ib = interpolate_batch(batch, 3)
    assert ib.label == "my-label"


def test_interpolate_batch_invalid_target_raises():
    batch = make_batch("cmd", [1.0])
    with pytest.raises(ValueError):
        interpolate_batch(batch, 0)


def test_interpolate_batch_success_count_all_ok():
    batch = make_batch("cmd", [1.0, 2.0])
    ib = interpolate_batch(batch, 4)
    assert ib.success_count == ib.total


# --- interpolate ---

def test_interpolate_result_count():
    batches = [make_batch("a", [1.0, 2.0]), make_batch("b", [3.0, 4.0])]
    result = interpolate(batches, 4)
    assert result.count == 2


def test_interpolate_total_added():
    batches = [make_batch("a", [1.0, 2.0]), make_batch("b", [1.0])]
    result = interpolate(batches, 4)
    assert result.total_added > 0


def test_interpolate_empty_raises():
    with pytest.raises(ValueError):
        interpolate([], 4)


def test_interpolate_each_batch_reaches_target():
    batches = [make_batch("x", [0.0, 10.0])]
    result = interpolate(batches, 5)
    assert result.batches[0].total == 5


# --- format_interpolate_summary ---

def test_format_summary_contains_label():
    batches = [make_batch("my-cmd", [1.0, 2.0])]
    result = interpolate(batches, 4)
    text = format_interpolate_summary(result)
    assert "my-cmd" in text


def test_format_summary_contains_added_count():
    batches = [make_batch("cmd", [1.0, 2.0])]
    result = interpolate(batches, 4)
    text = format_interpolate_summary(result)
    assert "+" in text


def test_format_summary_header_mentions_batch_count():
    batches = [make_batch("a", [1.0]), make_batch("b", [2.0])]
    result = interpolate(batches, 3)
    text = format_interpolate_summary(result)
    assert "2 batch" in text
