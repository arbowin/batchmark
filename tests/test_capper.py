"""Tests for batchmark.capper."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.capper import (
    CappedBatch,
    CapResult,
    cap_batch,
    cap_all,
    format_cap_summary,
)


def make_batch(label: str, elapsed_times: list, returncodes=None) -> BatchResult:
    if returncodes is None:
        returncodes = [0] * len(elapsed_times)
    runs = [RunResult(elapsed=e, returncode=rc) for e, rc in zip(elapsed_times, returncodes)]
    return BatchResult(label=label, runs=runs)


# --- cap_batch ---

def test_cap_batch_no_runs_exceed_cap():
    batch = make_batch("fast", [0.1, 0.2, 0.3])
    result = cap_batch(batch, cap=1.0)
    assert result.capped_count == 0
    assert [r.elapsed for r in result.runs] == [0.1, 0.2, 0.3]


def test_cap_batch_all_runs_exceed_cap():
    batch = make_batch("slow", [2.0, 3.0, 5.0])
    result = cap_batch(batch, cap=1.0)
    assert result.capped_count == 3
    assert all(r.elapsed == 1.0 for r in result.runs)


def test_cap_batch_partial_capping():
    batch = make_batch("mixed", [0.5, 1.5, 0.8, 2.2])
    result = cap_batch(batch, cap=1.0)
    assert result.capped_count == 2
    assert result.runs[0].elapsed == 0.5
    assert result.runs[1].elapsed == 1.0
    assert result.runs[2].elapsed == 0.8
    assert result.runs[3].elapsed == 1.0


def test_cap_batch_preserves_returncode():
    batch = make_batch("rc", [2.0, 0.5], returncodes=[1, 0])
    result = cap_batch(batch, cap=1.0)
    assert result.runs[0].returncode == 1
    assert result.runs[1].returncode == 0


def test_cap_batch_preserves_label():
    batch = make_batch("my-label", [1.0])
    result = cap_batch(batch, cap=2.0)
    assert result.label == "my-label"


def test_cap_batch_invalid_cap_raises():
    batch = make_batch("x", [1.0])
    with pytest.raises(ValueError):
        cap_batch(batch, cap=0.0)
    with pytest.raises(ValueError):
        cap_batch(batch, cap=-1.0)


def test_cap_batch_total_equals_run_count():
    batch = make_batch("t", [0.1, 0.2, 0.3, 0.4])
    result = cap_batch(batch, cap=0.25)
    assert result.total == 4


def test_cap_batch_success_count_unchanged():
    batch = make_batch("sc", [2.0, 2.0, 2.0], returncodes=[0, 0, 1])
    result = cap_batch(batch, cap=1.0)
    assert result.success_count == 2


# --- cap_all ---

def test_cap_all_returns_cap_result():
    batches = [make_batch("a", [0.1, 2.0]), make_batch("b", [3.0, 0.5])]
    result = cap_all(batches, cap=1.0)
    assert isinstance(result, CapResult)
    assert len(result.batches) == 2


def test_cap_all_total_capped():
    batches = [make_batch("a", [2.0, 2.0]), make_batch("b", [0.1, 2.0])]
    result = cap_all(batches, cap=1.0)
    assert result.total_capped == 3


# --- format_cap_summary ---

def test_format_cap_summary_contains_label():
    batches = [make_batch("bench-x", [0.5, 1.5])]
    result = cap_all(batches, cap=1.0)
    summary = format_cap_summary(result)
    assert "bench-x" in summary


def test_format_cap_summary_contains_total_capped():
    batches = [make_batch("a", [2.0]), make_batch("b", [3.0])]
    result = cap_all(batches, cap=1.0)
    summary = format_cap_summary(result)
    assert "Total capped" in summary
    assert "2" in summary
