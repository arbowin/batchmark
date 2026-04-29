"""Tests for batchmark.padder."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.padder import (
    PaddedBatch,
    PadResult,
    pad_batch,
    pad_all,
    format_pad_summary,
)


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times, rc: int = 0) -> BatchResult:
    runs = [_run(t, rc) for t in times]
    return BatchResult(label=label, runs=runs)


# ---------------------------------------------------------------------------
# pad_batch — repeat strategy
# ---------------------------------------------------------------------------

def test_pad_batch_no_padding_needed():
    batch = make_batch("cmd", [1.0, 2.0, 3.0])
    result = pad_batch(batch, target=3)
    assert result.added_count == 0
    assert result.total == 3


def test_pad_batch_repeat_fills_to_target():
    batch = make_batch("cmd", [1.0, 2.0])
    result = pad_batch(batch, target=5, strategy="repeat")
    assert result.total == 5
    assert result.added_count == 3


def test_pad_batch_repeat_cycles_in_order():
    batch = make_batch("cmd", [1.0, 2.0])
    result = pad_batch(batch, target=4, strategy="repeat")
    elapsed = [r.elapsed for r in result.runs]
    assert elapsed == [1.0, 2.0, 1.0, 2.0]


def test_pad_batch_truncates_when_over_target():
    batch = make_batch("cmd", [1.0, 2.0, 3.0, 4.0])
    result = pad_batch(batch, target=2)
    assert result.total == 2
    assert result.added_count == 0
    assert result.original_count == 4


# ---------------------------------------------------------------------------
# pad_batch — mean strategy
# ---------------------------------------------------------------------------

def test_pad_batch_mean_fills_to_target():
    batch = make_batch("cmd", [1.0, 3.0])
    result = pad_batch(batch, target=4, strategy="mean")
    assert result.total == 4
    assert result.added_count == 2


def test_pad_batch_mean_synthetic_elapsed_is_mean():
    batch = make_batch("cmd", [1.0, 3.0])
    result = pad_batch(batch, target=3, strategy="mean")
    synthetic = result.runs[2]
    assert synthetic.elapsed == pytest.approx(2.0)


def test_pad_batch_mean_synthetic_returncode_zero():
    batch = make_batch("cmd", [1.0, 2.0], rc=1)
    result = pad_batch(batch, target=3, strategy="mean")
    assert result.runs[2].returncode == 0


def test_pad_batch_unknown_strategy_raises():
    batch = make_batch("cmd", [1.0])
    with pytest.raises(ValueError, match="Unknown padding strategy"):
        pad_batch(batch, target=3, strategy="bogus")


def test_pad_batch_invalid_target_raises():
    batch = make_batch("cmd", [1.0])
    with pytest.raises(ValueError, match="target must be"):
        pad_batch(batch, target=0)


# ---------------------------------------------------------------------------
# pad_all
# ---------------------------------------------------------------------------

def test_pad_all_returns_pad_result():
    batches = [make_batch("a", [1.0]), make_batch("b", [2.0, 3.0])]
    result = pad_all(batches, target=3)
    assert isinstance(result, PadResult)
    assert len(result.batches) == 2


def test_pad_all_total_added():
    batches = [make_batch("a", [1.0]), make_batch("b", [1.0, 2.0])]
    result = pad_all(batches, target=4)
    assert result.total_added == 3 + 2


# ---------------------------------------------------------------------------
# format_pad_summary
# ---------------------------------------------------------------------------

def test_format_pad_summary_contains_header():
    batches = [make_batch("cmd", [1.0, 2.0])]
    result = pad_all(batches, target=4)
    text = format_pad_summary(result)
    assert "Padding summary" in text


def test_format_pad_summary_contains_label():
    batches = [make_batch("my-command", [1.0])]
    result = pad_all(batches, target=3)
    text = format_pad_summary(result)
    assert "my-command" in text


def test_format_pad_summary_contains_total_added():
    batches = [make_batch("x", [1.0])]
    result = pad_all(batches, target=5)
    text = format_pad_summary(result)
    assert "Total runs added" in text
    assert "4" in text
