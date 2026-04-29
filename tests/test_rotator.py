"""Tests for batchmark.rotator."""
from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.rotator import (
    RotatedBatch,
    RotateResult,
    _rotate,
    rotate_batch,
    rotate_all,
    format_rotate_summary,
)


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times: list[float]) -> BatchResult:
    runs = [_run(t) for t in times]
    return BatchResult(label=label, runs=runs)


# ---------------------------------------------------------------------------
# _rotate
# ---------------------------------------------------------------------------

def test_rotate_shift_zero_unchanged():
    runs = [_run(t) for t in [1.0, 2.0, 3.0]]
    assert _rotate(runs, 0) == runs


def test_rotate_shift_one():
    runs = [_run(t) for t in [1.0, 2.0, 3.0]]
    result = _rotate(runs, 1)
    assert [r.elapsed for r in result] == [2.0, 3.0, 1.0]


def test_rotate_shift_equals_length_is_identity():
    runs = [_run(t) for t in [1.0, 2.0, 3.0]]
    assert _rotate(runs, 3) == runs


def test_rotate_empty_returns_empty():
    assert _rotate([], 5) == []


# ---------------------------------------------------------------------------
# rotate_batch
# ---------------------------------------------------------------------------

def test_rotate_batch_label_preserved():
    batch = make_batch("cmd", [1.0, 2.0, 3.0])
    rb = rotate_batch(batch, 1)
    assert rb.label == "cmd"


def test_rotate_batch_shift_stored():
    batch = make_batch("cmd", [1.0, 2.0, 3.0])
    rb = rotate_batch(batch, 2)
    assert rb.shift == 2


def test_rotate_batch_total():
    batch = make_batch("cmd", [1.0, 2.0, 3.0])
    rb = rotate_batch(batch, 1)
    assert rb.total == 3


def test_rotate_batch_negative_shift_raises():
    batch = make_batch("cmd", [1.0, 2.0])
    with pytest.raises(ValueError, match="non-negative"):
        rotate_batch(batch, -1)


# ---------------------------------------------------------------------------
# rotate_all
# ---------------------------------------------------------------------------

def test_rotate_all_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        rotate_all([])


def test_rotate_all_returns_rotate_result():
    batches = [make_batch("a", [1.0, 2.0])]
    result = rotate_all(batches, shift=1)
    assert isinstance(result, RotateResult)


def test_rotate_all_count_matches_batches():
    batches = [make_batch("a", [1.0, 2.0]), make_batch("b", [3.0, 4.0])]
    result = rotate_all(batches, shift=1)
    assert result.count == 2


def test_rotate_all_per_batch_mismatched_length_raises():
    batches = [make_batch("a", [1.0, 2.0]), make_batch("b", [3.0, 4.0])]
    with pytest.raises(ValueError, match="per_batch length"):
        rotate_all(batches, per_batch=[1])


def test_rotate_all_per_batch_applies_individual_shifts():
    batches = [
        make_batch("a", [1.0, 2.0, 3.0]),
        make_batch("b", [4.0, 5.0, 6.0]),
    ]
    result = rotate_all(batches, per_batch=[1, 2])
    assert result.batches[0].shift == 1
    assert result.batches[1].shift == 2
    assert result.batches[0].runs[0].elapsed == 2.0
    assert result.batches[1].runs[0].elapsed == 6.0


# ---------------------------------------------------------------------------
# format_rotate_summary
# ---------------------------------------------------------------------------

def test_format_rotate_summary_contains_label():
    batches = [make_batch("myjob", [1.0, 2.0])]
    result = rotate_all(batches, shift=1)
    summary = format_rotate_summary(result)
    assert "myjob" in summary


def test_format_rotate_summary_contains_shift():
    batches = [make_batch("myjob", [1.0, 2.0])]
    result = rotate_all(batches, shift=1)
    summary = format_rotate_summary(result)
    assert "shift=1" in summary
