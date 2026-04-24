"""Tests for batchmark.splitter."""

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.splitter import (
    SplitResult,
    format_split,
    split_all,
    split_batch,
)


def make_batch(label: str, n: int) -> BatchResult:
    runs = [RunResult(elapsed=float(i), returncode=0, stdout="", stderr="") for i in range(n)]
    return BatchResult(label=label, runs=runs)


def test_split_batch_label_preserved():
    batch = make_batch("cmd_a", 10)
    result = split_batch(batch, ratio=0.8)
    assert result.label == "cmd_a"


def test_split_batch_train_count():
    batch = make_batch("cmd_a", 10)
    result = split_batch(batch, ratio=0.8)
    assert result.train[0].run_count == 8


def test_split_batch_test_count():
    batch = make_batch("cmd_a", 10)
    result = split_batch(batch, ratio=0.8)
    assert result.test[0].run_count == 2


def test_split_batch_total_runs_preserved():
    batch = make_batch("cmd_b", 10)
    result = split_batch(batch, ratio=0.7)
    total_runs = result.train[0].run_count + result.test[0].run_count
    assert total_runs == 10


def test_split_batch_invalid_ratio_zero():
    batch = make_batch("x", 5)
    with pytest.raises(ValueError):
        split_batch(batch, ratio=0.0)


def test_split_batch_invalid_ratio_one():
    batch = make_batch("x", 5)
    with pytest.raises(ValueError):
        split_batch(batch, ratio=1.0)


def test_split_batch_single_run_goes_to_train():
    batch = make_batch("solo", 1)
    result = split_batch(batch, ratio=0.8)
    assert result.train[0].run_count == 1
    assert result.test[0].run_count == 0


def test_split_all_returns_one_per_batch():
    batches = [make_batch(f"cmd_{i}", 10) for i in range(3)]
    results = split_all(batches, ratio=0.8)
    assert len(results) == 3


def test_split_all_empty_raises():
    with pytest.raises(ValueError):
        split_all([])


def test_split_all_labels_match():
    batches = [make_batch("alpha", 8), make_batch("beta", 8)]
    results = split_all(batches, ratio=0.75)
    labels = [r.label for r in results]
    assert labels == ["alpha", "beta"]


def test_split_result_total_property():
    batch = make_batch("t", 10)
    result = split_batch(batch)
    assert result.total == result.train_count + result.test_count


def test_format_split_contains_label():
    batch = make_batch("my_cmd", 10)
    result = split_batch(batch)
    output = format_split(result)
    assert "my_cmd" in output


def test_format_split_contains_train_test():
    batch = make_batch("my_cmd", 10)
    result = split_batch(batch)
    output = format_split(result)
    assert "train" in output
    assert "test" in output
