"""Tests for batchmark.truncator."""
from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.truncator import (
    TruncatedBatch,
    TruncateResult,
    _truncate_batch,
    format_truncate_summary,
    truncate,
)


def _run(elapsed: float = 1.0, returncode: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=returncode, stdout="", stderr="")


def make_batch(label: str, count: int, returncode: int = 0) -> BatchResult:
    return BatchResult(label=label, runs=[_run(float(i + 1), returncode) for i in range(count)])


# --- TruncatedBatch properties ---

def test_truncated_batch_total():
    tb = TruncatedBatch(label="a", runs=[_run(), _run()])
    assert tb.total == 2


def test_truncated_batch_success_count_all_ok():
    tb = TruncatedBatch(label="a", runs=[_run(returncode=0)] * 3)
    assert tb.success_count == 3


def test_truncated_batch_success_count_partial():
    tb = TruncatedBatch(label="a", runs=[_run(returncode=0), _run(returncode=1)])
    assert tb.success_count == 1


# --- _truncate_batch ---

def test_truncate_batch_keeps_up_to_max():
    batch = make_batch("x", 10)
    tb = _truncate_batch(batch, 5)
    assert tb.total == 5


def test_truncate_batch_no_removal_when_under_max():
    batch = make_batch("x", 3)
    tb = _truncate_batch(batch, 10)
    assert tb.total == 3


def test_truncate_batch_preserves_label():
    batch = make_batch("my-label", 5)
    tb = _truncate_batch(batch, 3)
    assert tb.label == "my-label"


def test_truncate_batch_preserves_order():
    batch = make_batch("x", 5)
    tb = _truncate_batch(batch, 3)
    assert [r.elapsed for r in tb.runs] == [1.0, 2.0, 3.0]


def test_truncate_batch_invalid_max_raises():
    batch = make_batch("x", 5)
    with pytest.raises(ValueError):
        _truncate_batch(batch, 0)


# --- truncate ---

def test_truncate_returns_truncate_result():
    batches = [make_batch("a", 8)]
    result = truncate(batches, 5)
    assert isinstance(result, TruncateResult)


def test_truncate_count_matches_input():
    batches = [make_batch("a", 8), make_batch("b", 6)]
    result = truncate(batches, 4)
    assert result.count == 2


def test_truncate_all_batches_trimmed():
    batches = [make_batch("a", 8), make_batch("b", 6)]
    result = truncate(batches, 4)
    assert all(tb.total <= 4 for tb in result.batches)


def test_truncate_max_runs_stored():
    result = truncate([make_batch("a", 5)], 3)
    assert result.max_runs == 3


def test_truncate_empty_raises():
    with pytest.raises(ValueError):
        truncate([], 5)


def test_truncate_invalid_max_raises():
    with pytest.raises(ValueError):
        truncate([make_batch("a", 5)], -1)


# --- format_truncate_summary ---

def test_format_summary_contains_label():
    result = truncate([make_batch("my-cmd", 10)], 5)
    summary = format_truncate_summary(result)
    assert "my-cmd" in summary


def test_format_summary_contains_max_runs():
    result = truncate([make_batch("a", 10)], 7)
    summary = format_truncate_summary(result)
    assert "7" in summary


def test_format_summary_shows_removed_count():
    result = truncate([make_batch("a", 10)], 6)
    summary = format_truncate_summary(result)
    assert "4 removed" in summary


def test_format_summary_no_removed_when_under_max():
    result = truncate([make_batch("a", 3)], 10)
    summary = format_truncate_summary(result)
    assert "removed" not in summary
