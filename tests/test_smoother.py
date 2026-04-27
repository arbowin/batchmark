"""Tests for batchmark.smoother."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.smoother import (
    SmoothedBatch,
    SmoothedPoint,
    SmoothResult,
    _chunk_means,
    _rolling_average,
    format_smooth,
    smooth,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times: list[float]) -> BatchResult:
    return BatchResult(label=label, results=[_run(t) for t in times])


# ---------------------------------------------------------------------------
# _chunk_means
# ---------------------------------------------------------------------------

def test_chunk_means_single_window():
    batch = make_batch("x", [1.0, 2.0, 3.0])
    means = _chunk_means(batch, window=3)
    assert len(means) == 1
    assert means[0] == pytest.approx(2.0)


def test_chunk_means_multiple_windows():
    batch = make_batch("x", [1.0, 3.0, 2.0, 4.0])
    means = _chunk_means(batch, window=2)
    assert len(means) == 2
    assert means[0] == pytest.approx(2.0)
    assert means[1] == pytest.approx(3.0)


def test_chunk_means_empty_batch():
    batch = make_batch("x", [])
    assert _chunk_means(batch, window=3) == []


def test_chunk_means_partial_last_window():
    batch = make_batch("x", [1.0, 2.0, 3.0, 4.0, 5.0])
    means = _chunk_means(batch, window=3)
    # windows: [1,2,3] and [4,5]
    assert len(means) == 2
    assert means[1] == pytest.approx(4.5)


# ---------------------------------------------------------------------------
# _rolling_average
# ---------------------------------------------------------------------------

def test_rolling_average_span_one_is_identity():
    values = [1.0, 2.0, 3.0, 4.0]
    assert _rolling_average(values, span=1) == pytest.approx(values)


def test_rolling_average_span_larger_than_series():
    values = [2.0, 4.0]
    result = _rolling_average(values, span=10)
    assert result[0] == pytest.approx(2.0)
    assert result[1] == pytest.approx(3.0)


def test_rolling_average_empty():
    assert _rolling_average([], span=3) == []


def test_rolling_average_trailing_window():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = _rolling_average(values, span=3)
    # index 2 -> mean(1,2,3) = 2.0
    assert result[2] == pytest.approx(2.0)
    # index 4 -> mean(3,4,5) = 4.0
    assert result[4] == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# smooth
# ---------------------------------------------------------------------------

def test_smooth_returns_smooth_result():
    batches = [make_batch("cmd", [1.0] * 10)]
    result = smooth(batches)
    assert isinstance(result, SmoothResult)


def test_smooth_labels_preserved():
    batches = [make_batch("alpha", [1.0] * 6), make_batch("beta", [2.0] * 6)]
    result = smooth(batches)
    assert result.labels == ["alpha", "beta"]


def test_smooth_point_count():
    # 10 runs, chunk_size=2 -> 5 raw points
    batches = [make_batch("cmd", [1.0] * 10)]
    result = smooth(batches, chunk_size=2, span=2)
    assert len(result.batches[0].points) == 5


def test_smooth_constant_series_unchanged():
    batches = [make_batch("cmd", [3.0] * 9)]
    result = smooth(batches, chunk_size=3, span=3)
    for p in result.batches[0].points:
        assert p.smoothed_mean == pytest.approx(3.0)
        assert p.raw_mean == pytest.approx(3.0)


def test_smooth_invalid_chunk_size_raises():
    with pytest.raises(ValueError, match="chunk_size"):
        smooth([], chunk_size=0)


def test_smooth_invalid_span_raises():
    with pytest.raises(ValueError, match="span"):
        smooth([], span=0)


def test_smooth_empty_batch_produces_no_points():
    batches = [make_batch("empty", [])]
    result = smooth(batches)
    assert result.batches[0].points == []


# ---------------------------------------------------------------------------
# format_smooth
# ---------------------------------------------------------------------------

def test_format_smooth_contains_label():
    batches = [make_batch("mycmd", [1.0] * 6)]
    result = smooth(batches, chunk_size=2, span=2)
    text = format_smooth(result)
    assert "mycmd" in text


def test_format_smooth_contains_raw_and_smooth():
    batches = [make_batch("cmd", [1.0] * 6)]
    result = smooth(batches, chunk_size=2, span=2)
    text = format_smooth(result)
    assert "raw=" in text
    assert "smooth=" in text


def test_format_smooth_empty_batch_shows_no_data():
    batches = [make_batch("empty", [])]
    result = smooth(batches)
    text = format_smooth(result)
    assert "(no data)" in text
