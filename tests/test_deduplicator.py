"""Tests for batchmark.deduplicator."""

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.deduplicator import (
    deduplicate,
    format_deduplication,
    _is_duplicate,
    _batch_mean,
)


def make_batch(label: str, times: list, successes: int = None) -> BatchResult:
    runs = [
        RunResult(elapsed=t, returncode=0, stdout="", stderr="")
        for t in times
    ]
    if successes is None:
        successes = len(runs)
    return BatchResult(label=label, runs=runs)


# --- _batch_mean ---

def test_batch_mean_basic():
    b = make_batch("a", [1.0, 2.0, 3.0])
    assert _batch_mean(b) == pytest.approx(2.0)


def test_batch_mean_empty():
    b = BatchResult(label="empty", runs=[])
    assert _batch_mean(b) == 0.0


# --- _is_duplicate ---

def test_is_duplicate_same_label_same_time():
    a = make_batch("cmd", [1.0, 1.0])
    b = make_batch("cmd", [1.0, 1.0])
    assert _is_duplicate(a, b) is True


def test_is_duplicate_different_labels():
    a = make_batch("cmd1", [1.0])
    b = make_batch("cmd2", [1.0])
    assert _is_duplicate(a, b) is False


def test_is_duplicate_same_label_different_time():
    a = make_batch("cmd", [1.0])
    b = make_batch("cmd", [2.0])
    assert _is_duplicate(a, b) is False


def test_is_duplicate_within_tolerance():
    a = make_batch("cmd", [1.000])
    b = make_batch("cmd", [1.005])  # 0.5% difference
    assert _is_duplicate(a, b, time_tolerance=0.01) is True


def test_is_duplicate_exceeds_tolerance():
    a = make_batch("cmd", [1.0])
    b = make_batch("cmd", [1.05])  # 5% difference
    assert _is_duplicate(a, b, time_tolerance=0.01) is False


# --- deduplicate ---

def test_deduplicate_empty():
    result = deduplicate([])
    assert result.kept == []
    assert result.removed == []
    assert result.total_before == 0
    assert result.total_after == 0


def test_deduplicate_no_duplicates():
    batches = [make_batch("a", [1.0]), make_batch("b", [2.0])]
    result = deduplicate(batches)
    assert len(result.kept) == 2
    assert result.removed_count == 0


def test_deduplicate_removes_exact_duplicate():
    a = make_batch("cmd", [1.0, 1.0])
    b = make_batch("cmd", [1.0, 1.0])
    result = deduplicate([a, b])
    assert len(result.kept) == 1
    assert result.removed_count == 1
    assert result.kept[0] is a


def test_deduplicate_keeps_different_labels():
    a = make_batch("cmd1", [1.0])
    b = make_batch("cmd2", [1.0])
    result = deduplicate([a, b])
    assert len(result.kept) == 2


def test_deduplicate_total_counts():
    batches = [make_batch("x", [1.0])] * 3
    result = deduplicate(batches)
    assert result.total_before == 3
    assert result.total_after == 1


# --- format_deduplication ---

def test_format_deduplication_contains_summary():
    batches = [make_batch("cmd", [1.0]), make_batch("cmd", [1.0])]
    result = deduplicate(batches)
    text = format_deduplication(result)
    assert "Deduplication" in text
    assert "Before" in text
    assert "After" in text


def test_format_deduplication_lists_removed_labels():
    batches = [make_batch("slow", [2.0]), make_batch("slow", [2.0])]
    result = deduplicate(batches)
    text = format_deduplication(result)
    assert "slow" in text
