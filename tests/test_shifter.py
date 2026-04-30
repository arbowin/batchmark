"""Tests for batchmark.shifter and batchmark.shift_cli."""
from __future__ import annotations

import json
import os
import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.shifter import (
    ShiftedBatch,
    ShiftResult,
    format_shift_summary,
    shift_all,
    shift_batch,
)


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(command="echo hi", elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times, rcs=None) -> BatchResult:
    if rcs is None:
        rcs = [0] * len(times)
    runs = [_run(t, rc) for t, rc in zip(times, rcs)]
    return BatchResult(label=label, runs=runs)


# --- shift_batch ---

def test_shift_batch_label_preserved():
    b = make_batch("cmd", [1.0, 2.0])
    sb = shift_batch(b, offset=0.0, scale=1.0)
    assert sb.label == "cmd"


def test_shift_batch_offset_added():
    b = make_batch("cmd", [1.0, 2.0])
    sb = shift_batch(b, offset=0.5)
    assert sb.runs[0].elapsed == pytest.approx(1.5)
    assert sb.runs[1].elapsed == pytest.approx(2.5)


def test_shift_batch_scale_applied():
    b = make_batch("cmd", [2.0, 4.0])
    sb = shift_batch(b, scale=2.0)
    assert sb.runs[0].elapsed == pytest.approx(4.0)
    assert sb.runs[1].elapsed == pytest.approx(8.0)


def test_shift_batch_scale_then_offset():
    b = make_batch("cmd", [2.0])
    sb = shift_batch(b, offset=1.0, scale=3.0)
    # 2.0 * 3.0 + 1.0 == 7.0
    assert sb.runs[0].elapsed == pytest.approx(7.0)


def test_shift_batch_clamps_to_zero():
    b = make_batch("cmd", [0.5])
    sb = shift_batch(b, offset=-10.0)
    assert sb.runs[0].elapsed == 0.0


def test_shift_batch_negative_scale_raises():
    b = make_batch("cmd", [1.0])
    with pytest.raises(ValueError, match="scale"):
        shift_batch(b, scale=-1.0)


def test_shift_batch_returncode_preserved():
    b = make_batch("cmd", [1.0, 2.0], rcs=[0, 1])
    sb = shift_batch(b)
    assert sb.runs[0].returncode == 0
    assert sb.runs[1].returncode == 1


def test_shift_batch_total():
    b = make_batch("cmd", [1.0, 2.0, 3.0])
    sb = shift_batch(b)
    assert sb.total == 3


def test_shift_batch_success_count():
    b = make_batch("cmd", [1.0, 2.0], rcs=[0, 1])
    sb = shift_batch(b)
    assert sb.success_count == 1


# --- shift_all ---

def test_shift_all_empty_raises():
    with pytest.raises(ValueError):
        shift_all([])


def test_shift_all_returns_shift_result():
    batches = [make_batch("a", [1.0]), make_batch("b", [2.0])]
    result = shift_all(batches, offset=0.1)
    assert isinstance(result, ShiftResult)


def test_shift_all_count():
    batches = [make_batch("a", [1.0]), make_batch("b", [2.0])]
    result = shift_all(batches)
    assert result.count == 2


def test_shift_all_applies_to_each_batch():
    batches = [make_batch("a", [1.0]), make_batch("b", [3.0])]
    result = shift_all(batches, scale=2.0)
    assert result.batches[0].runs[0].elapsed == pytest.approx(2.0)
    assert result.batches[1].runs[0].elapsed == pytest.approx(6.0)


# --- format_shift_summary ---

def test_format_shift_summary_contains_header():
    batches = [make_batch("cmd", [1.0])]
    result = shift_all(batches)
    text = format_shift_summary(result)
    assert "Shift Summary" in text


def test_format_shift_summary_contains_label():
    batches = [make_batch("myjob", [1.0, 2.0])]
    result = shift_all(batches)
    text = format_shift_summary(result)
    assert "myjob" in text


def test_format_shift_summary_shows_run_count():
    batches = [make_batch("myjob", [1.0, 2.0, 3.0])]
    result = shift_all(batches)
    text = format_shift_summary(result)
    assert "3 runs" in text
