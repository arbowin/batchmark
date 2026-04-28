"""Tests for batchmark.sorter."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.sorter import (
    SortResult,
    format_sort_result,
    sort_batches,
)


def make_batch(label: str, elapsed: list[float], failures: int = 0) -> BatchResult:
    runs = [RunResult(elapsed=e, returncode=0, stdout="", stderr="") for e in elapsed]
    for i in range(failures):
        runs[i] = RunResult(elapsed=runs[i].elapsed, returncode=1, stdout="", stderr="")
    return BatchResult(label=label, runs=runs)


def test_sort_by_mean_ascending():
    batches = [
        make_batch("slow", [2.0, 3.0]),
        make_batch("fast", [0.5, 0.6]),
        make_batch("mid", [1.0, 1.2]),
    ]
    result = sort_batches(batches, key="mean", order="asc")
    labels = [b.label for b in result.batches]
    assert labels == ["fast", "mid", "slow"]


def test_sort_by_mean_descending():
    batches = [
        make_batch("slow", [2.0, 3.0]),
        make_batch("fast", [0.5, 0.6]),
    ]
    result = sort_batches(batches, key="mean", order="desc")
    assert result.batches[0].label == "slow"


def test_sort_by_label_alphabetical():
    batches = [
        make_batch("zebra", [1.0]),
        make_batch("apple", [2.0]),
        make_batch("mango", [1.5]),
    ]
    result = sort_batches(batches, key="label", order="asc")
    assert [b.label for b in result.batches] == ["apple", "mango", "zebra"]


def test_sort_by_success_rate_descending():
    batches = [
        make_batch("partial", [1.0, 1.0, 1.0, 1.0], failures=2),
        make_batch("perfect", [1.0, 1.0]),
        make_batch("worst", [1.0, 1.0, 1.0, 1.0], failures=4),
    ]
    result = sort_batches(batches, key="success_rate", order="desc")
    assert result.batches[0].label == "perfect"
    assert result.batches[-1].label == "worst"


def test_sort_by_total_runs():
    batches = [
        make_batch("few", [1.0, 2.0]),
        make_batch("many", [1.0] * 10),
        make_batch("one", [1.0]),
    ]
    result = sort_batches(batches, key="total", order="asc")
    assert result.batches[0].label == "one"
    assert result.batches[-1].label == "many"


def test_sort_by_median():
    batches = [
        make_batch("b", [1.0, 5.0, 5.0]),
        make_batch("a", [0.1, 0.2, 0.3]),
    ]
    result = sort_batches(batches, key="median", order="asc")
    assert result.batches[0].label == "a"


def test_sort_result_stores_key_and_order():
    batches = [make_batch("x", [1.0])]
    result = sort_batches(batches, key="mean", order="desc")
    assert result.key == "mean"
    assert result.order == "desc"


def test_sort_result_len():
    batches = [make_batch(f"cmd{i}", [float(i)]) for i in range(5)]
    result = sort_batches(batches)
    assert len(result) == 5


def test_sort_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        sort_batches([])


def test_format_sort_result_contains_label():
    batches = [make_batch("my-cmd", [1.0, 2.0])]
    result = sort_batches(batches)
    text = format_sort_result(result)
    assert "my-cmd" in text


def test_format_sort_result_contains_key():
    batches = [make_batch("cmd", [1.0])]
    result = sort_batches(batches, key="median")
    text = format_sort_result(result)
    assert "median" in text
