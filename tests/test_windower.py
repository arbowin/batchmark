"""Tests for batchmark.windower."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.windower import WindowResult, WindowStats, format_window_result, slide


def _run(elapsed: float, ok: bool = True) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=0 if ok else 1, stdout="", stderr="")


def _batch(label: str, *times: float, ok: bool = True) -> BatchResult:
    return BatchResult(label=label, runs=[_run(t, ok) for t in times])


# ---------------------------------------------------------------------------
# slide — basic behaviour
# ---------------------------------------------------------------------------

def test_slide_returns_window_result_per_label():
    batches = [_batch("cmd", 1.0), _batch("cmd", 2.0), _batch("cmd", 3.0)]
    results = slide(batches, window_size=2)
    assert len(results) == 1
    assert results[0].label == "cmd"


def test_slide_correct_window_count():
    batches = [_batch("cmd", float(i)) for i in range(5)]
    results = slide(batches, window_size=3)
    # 5 batches, window=3 → 3 windows
    assert results[0].count == 3


def test_slide_window_size_one_equals_batch_count():
    batches = [_batch("x", 1.0), _batch("x", 2.0), _batch("x", 3.0)]
    results = slide(batches, window_size=1)
    assert results[0].count == 3


def test_slide_window_size_equals_batch_count_gives_one_window():
    batches = [_batch("x", 1.0), _batch("x", 2.0), _batch("x", 3.0)]
    results = slide(batches, window_size=3)
    assert results[0].count == 1


def test_slide_mean_values():
    batches = [_batch("cmd", 1.0), _batch("cmd", 3.0), _batch("cmd", 5.0)]
    results = slide(batches, window_size=2)
    means = results[0].means()
    assert abs(means[0] - 2.0) < 1e-9  # (1+3)/2
    assert abs(means[1] - 4.0) < 1e-9  # (3+5)/2


def test_slide_start_end_indices():
    batches = [_batch("a", float(i)) for i in range(4)]
    windows = slide(batches, window_size=2)[0].windows
    assert windows[0].start == 0 and windows[0].end == 1
    assert windows[1].start == 1 and windows[1].end == 2
    assert windows[2].start == 2 and windows[2].end == 3


def test_slide_success_count():
    b1 = BatchResult(label="x", runs=[_run(1.0, ok=True), _run(2.0, ok=False)])
    b2 = BatchResult(label="x", runs=[_run(1.5, ok=True), _run(1.5, ok=True)])
    results = slide([b1, b2], window_size=2)
    w = results[0].windows[0]
    assert w.success_count == 3
    assert w.run_count == 4


def test_slide_success_rate_all_ok():
    batches = [_batch("y", 1.0, 2.0), _batch("y", 3.0)]
    w = slide(batches, window_size=2)[0].windows[0]
    assert w.success_rate == pytest.approx(1.0)


def test_slide_separates_labels():
    batches = [
        _batch("a", 1.0), _batch("a", 2.0),
        _batch("b", 5.0), _batch("b", 6.0),
    ]
    results = slide(batches, window_size=2)
    labels = {r.label for r in results}
    assert labels == {"a", "b"}


# ---------------------------------------------------------------------------
# slide — error cases
# ---------------------------------------------------------------------------

def test_slide_invalid_window_size_raises():
    with pytest.raises(ValueError, match="window_size"):
        slide([_batch("x", 1.0)], window_size=0)


def test_slide_empty_batches_raises():
    with pytest.raises(ValueError):
        slide([], window_size=1)


# ---------------------------------------------------------------------------
# format_window_result
# ---------------------------------------------------------------------------

def test_format_window_result_contains_label():
    batches = [_batch("mycmd", 1.0), _batch("mycmd", 2.0)]
    wr = slide(batches, window_size=2)[0]
    out = format_window_result(wr)
    assert "mycmd" in out


def test_format_window_result_contains_mean():
    batches = [_batch("cmd", 2.0), _batch("cmd", 4.0)]
    wr = slide(batches, window_size=2)[0]
    out = format_window_result(wr)
    assert "3.0000" in out


def test_format_window_result_row_per_window():
    batches = [_batch("cmd", float(i)) for i in range(4)]
    wr = slide(batches, window_size=2)[0]
    out = format_window_result(wr)
    # 3 data rows + 2 header lines = at least 5 lines
    lines = [l for l in out.splitlines() if l.strip()]
    assert len(lines) >= 5
