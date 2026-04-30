"""Tests for batchmark.cutter."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.cutter import (
    CutBatch,
    CutResult,
    cut_batch,
    cut_all,
    format_cut_summary,
)


def _run(elapsed: float, returncode: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=returncode, stdout="", stderr="")


def make_batch(label: str, times, codes=None) -> BatchResult:
    if codes is None:
        codes = [0] * len(times)
    runs = [_run(t, c) for t, c in zip(times, codes)]
    return BatchResult(label=label, runs=runs)


# --- cut_batch ---

def test_cut_batch_label_preserved():
    b = make_batch("cmd", [1.0, 2.0, 3.0, 4.0, 5.0])
    cb = cut_batch(b, 1, 4)
    assert cb.label == "cmd"


def test_cut_batch_correct_run_count():
    b = make_batch("cmd", [1.0, 2.0, 3.0, 4.0, 5.0])
    cb = cut_batch(b, 0, 3)
    assert cb.total == 3


def test_cut_batch_selects_correct_runs():
    b = make_batch("cmd", [1.0, 2.0, 3.0, 4.0, 5.0])
    cb = cut_batch(b, 2, 4)
    assert [r.elapsed for r in cb.runs] == [3.0, 4.0]


def test_cut_batch_empty_slice():
    b = make_batch("cmd", [1.0, 2.0, 3.0])
    cb = cut_batch(b, 1, 1)
    assert cb.total == 0


def test_cut_batch_success_count():
    b = make_batch("cmd", [1.0, 2.0, 3.0, 4.0], codes=[0, 1, 0, 1])
    cb = cut_batch(b, 0, 4)
    assert cb.success_count == 2


def test_cut_batch_invalid_start_raises():
    b = make_batch("cmd", [1.0, 2.0])
    with pytest.raises(ValueError, match="start must be >= 0"):
        cut_batch(b, -1, 2)


def test_cut_batch_stop_before_start_raises():
    b = make_batch("cmd", [1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match="stop must be >= start"):
        cut_batch(b, 3, 1)


def test_cut_batch_start_exceeds_size_raises():
    b = make_batch("cmd", [1.0, 2.0])
    with pytest.raises(ValueError, match="exceeds batch size"):
        cut_batch(b, 10, 12)


# --- cut_all ---

def test_cut_all_returns_cut_result():
    batches = [make_batch("a", [1.0, 2.0, 3.0]), make_batch("b", [4.0, 5.0, 6.0])]
    result = cut_all(batches, 0, 2)
    assert isinstance(result, CutResult)


def test_cut_all_count_matches_input():
    batches = [make_batch("a", [1.0, 2.0, 3.0]), make_batch("b", [4.0, 5.0, 6.0])]
    result = cut_all(batches, 1, 3)
    assert result.count == 2


def test_cut_all_stores_start_stop():
    batches = [make_batch("x", [1.0, 2.0, 3.0, 4.0])]
    result = cut_all(batches, 1, 3)
    assert result.start == 1
    assert result.stop == 3


def test_cut_all_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        cut_all([], 0, 2)


# --- format_cut_summary ---

def test_format_cut_summary_contains_range():
    batches = [make_batch("cmd", [1.0, 2.0, 3.0])]
    result = cut_all(batches, 0, 2)
    text = format_cut_summary(result)
    assert "[0:2]" in text


def test_format_cut_summary_contains_label():
    batches = [make_batch("myscript", [1.0, 2.0, 3.0])]
    result = cut_all(batches, 0, 3)
    text = format_cut_summary(result)
    assert "myscript" in text


def test_format_cut_summary_contains_run_count():
    batches = [make_batch("cmd", [1.0, 2.0, 3.0, 4.0, 5.0])]
    result = cut_all(batches, 1, 4)
    text = format_cut_summary(result)
    assert "3 run" in text
