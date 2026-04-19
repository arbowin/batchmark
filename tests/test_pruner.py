"""Tests for batchmark.pruner."""
import pytest
from batchmark.pruner import (
    prune_by_age,
    prune_by_success_rate,
    prune,
    format_prune_result,
)
from batchmark.history import HistoryEntry


def make_entry(label: str, timestamp: str, successes: int = 5, total: int = 5) -> HistoryEntry:
    return HistoryEntry(
        label=label,
        timestamp=timestamp,
        mean=1.0,
        median=1.0,
        stdev=0.0,
        successes=successes,
        total=total,
    )


def test_prune_by_age_keeps_most_recent():
    entries = [
        make_entry("a", "2024-01-01T00:00:00"),
        make_entry("a", "2024-01-03T00:00:00"),
        make_entry("a", "2024-01-02T00:00:00"),
    ]
    result = prune_by_age(entries, keep_last=2)
    timestamps = sorted(e.timestamp for e in result.kept)
    assert "2024-01-03T00:00:00" in timestamps
    assert "2024-01-02T00:00:00" in timestamps
    assert len(result.removed) == 1


def test_prune_by_age_separate_labels():
    entries = [
        make_entry("a", "2024-01-01T00:00:00"),
        make_entry("b", "2024-01-01T00:00:00"),
    ]
    result = prune_by_age(entries, keep_last=1)
    assert len(result.kept) == 2
    assert len(result.removed) == 0


def test_prune_by_success_rate_removes_low():
    entries = [
        make_entry("a", "2024-01-01T00:00:00", successes=1, total=10),
        make_entry("b", "2024-01-01T00:00:00", successes=9, total=10),
    ]
    result = prune_by_success_rate(entries, min_rate=0.5)
    assert len(result.kept) == 1
    assert result.kept[0].label == "b"
    assert len(result.removed) == 1


def test_prune_by_success_rate_keeps_all_when_threshold_zero():
    entries = [
        make_entry("a", "2024-01-01T00:00:00", successes=0, total=5),
    ]
    result = prune_by_success_rate(entries, min_rate=0.0)
    assert len(result.kept) == 1


def test_prune_combines_both_filters():
    entries = [
        make_entry("a", "2024-01-01T00:00:00", successes=5, total=5),
        make_entry("a", "2024-01-02T00:00:00", successes=5, total=5),
        make_entry("a", "2024-01-03T00:00:00", successes=1, total=10),
    ]
    result = prune(entries, keep_last=2, min_success_rate=0.5)
    assert len(result.kept) == 1
    assert result.kept[0].timestamp == "2024-01-02T00:00:00"
    assert len(result.removed) == 2


def test_format_prune_result_contains_counts():
    entries = [
        make_entry("a", "2024-01-01T00:00:00"),
        make_entry("a", "2024-01-02T00:00:00"),
    ]
    result = prune_by_age(entries, keep_last=1)
    text = format_prune_result(result)
    assert "Kept" in text
    assert "Removed" in text
    assert "1" in text
