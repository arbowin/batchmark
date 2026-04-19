"""Tests for batchmark.trend."""
import pytest

from batchmark.history import History, HistoryEntry
from batchmark.trend import TrendPoint, Trend, compute_trend, format_trend


def make_entry(label="cmd", mean=1.0, success_count=3, total=3, timestamp="2024-01-01T00:00:00+00:00"):
    return HistoryEntry(label=label, timestamp=timestamp, mean=mean, median=mean, stdev=0.0,
                        success_count=success_count, total=total)


def test_compute_trend_returns_none_for_missing_label():
    h = History(entries=[make_entry(label="other")])
    assert compute_trend("missing", h) is None


def test_compute_trend_label():
    h = History(entries=[make_entry(label="ls")])
    trend = compute_trend("ls", h)
    assert trend.label == "ls"


def test_compute_trend_point_count():
    h = History(entries=[make_entry(timestamp="t1"), make_entry(timestamp="t2")])
    trend = compute_trend("cmd", h)
    assert len(trend.points) == 2


def test_compute_trend_filters_by_label():
    h = History(entries=[make_entry(label="a"), make_entry(label="b"), make_entry(label="a")])
    trend = compute_trend("a", h)
    assert len(trend.points) == 2


def test_direction_improving():
    entries = [
        make_entry(mean=2.0, timestamp="t1"),
        make_entry(mean=1.0, timestamp="t2"),
    ]
    trend = compute_trend("cmd", History(entries=entries))
    assert trend.direction == "improving"


def test_direction_degrading():
    entries = [
        make_entry(mean=1.0, timestamp="t1"),
        make_entry(mean=2.0, timestamp="t2"),
    ]
    trend = compute_trend("cmd", History(entries=entries))
    assert trend.direction == "degrading"


def test_direction_stable():
    entries = [
        make_entry(mean=1.0, timestamp="t1"),
        make_entry(mean=1.01, timestamp="t2"),
    ]
    trend = compute_trend("cmd", History(entries=entries))
    assert trend.direction == "stable"


def test_direction_single_point():
    h = History(entries=[make_entry()])
    trend = compute_trend("cmd", h)
    assert trend.direction == "stable"


def test_success_rate_in_points():
    h = History(entries=[make_entry(success_count=2, total=4)])
    trend = compute_trend("cmd", h)
    assert trend.points[0].success_rate == pytest.approx(0.5)


def test_format_trend_contains_label():
    h = History(entries=[make_entry(label="echo")])
    trend = compute_trend("echo", h)
    out = format_trend(trend)
    assert "echo" in out


def test_format_trend_contains_direction():
    h = History(entries=[make_entry()])
    trend = compute_trend("cmd", h)
    out = format_trend(trend)
    assert trend.direction in out
