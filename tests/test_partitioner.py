"""Tests for batchmark.partitioner and partition_cli."""

from __future__ import annotations

import json
import os
import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.partitioner import (
    Partition,
    PartitionResult,
    partition_by_size,
    partition_by_count,
    format_partition_result,
)
from batchmark.partition_cli import build_partition_parser, main


def make_batch(label: str, times: list[float], successes: int | None = None) -> BatchResult:
    if successes is None:
        successes = len(times)
    runs = [
        RunResult(elapsed=t, returncode=0 if i < successes else 1)
        for i, t in enumerate(times)
    ]
    return BatchResult(label=label, runs=runs)


# --- partition_by_size ---

def test_partition_by_size_basic():
    batches = [make_batch(f"cmd{i}", [float(i)]) for i in range(5)]
    result = partition_by_size(batches, 2)
    assert result.strategy == "size"
    assert result.count() == 3


def test_partition_by_size_exact_fit():
    batches = [make_batch(f"cmd{i}", [1.0]) for i in range(4)]
    result = partition_by_size(batches, 2)
    assert result.count() == 2
    assert result.get(0).run_count() == 2


def test_partition_by_size_empty():
    result = partition_by_size([], 3)
    assert result.count() == 0
    assert result.partitions == []


def test_partition_by_size_invalid_raises():
    with pytest.raises(ValueError):
        partition_by_size([make_batch("a", [1.0])], 0)


def test_partition_by_size_indices():
    batches = [make_batch(f"c{i}", [1.0]) for i in range(3)]
    result = partition_by_size(batches, 1)
    for i, p in enumerate(result.partitions):
        assert p.index == i


# --- partition_by_count ---

def test_partition_by_count_basic():
    batches = [make_batch(f"cmd{i}", [float(i + 1)]) for i in range(6)]
    result = partition_by_count(batches, 3)
    assert result.strategy == "count"
    assert result.count() == 3


def test_partition_by_count_empty():
    result = partition_by_count([], 4)
    assert result.count() == 0


def test_partition_by_count_invalid_raises():
    with pytest.raises(ValueError):
        partition_by_count([make_batch("x", [1.0])], -1)


def test_partition_mean():
    b1 = make_batch("a", [1.0, 3.0])
    b2 = make_batch("b", [2.0, 4.0])
    p = Partition(index=0, batches=[b1, b2])
    assert p.mean() == pytest.approx(2.5)


def test_partition_labels():
    batches = [make_batch("alpha", [1.0]), make_batch("beta", [2.0])]
    result = partition_by_size(batches, 2)
    assert result.get(0).labels() == ["alpha", "beta"]


def test_partition_get_out_of_range():
    result = partition_by_size([make_batch("x", [1.0])], 1)
    with pytest.raises(IndexError):
        result.get(99)


# --- format ---

def test_format_partition_result_contains_strategy():
    batches = [make_batch("cmd", [0.5])]
    result = partition_by_size(batches, 1)
    text = format_partition_result(result)
    assert "size" in text
    assert "cmd" in text


# --- CLI ---

def test_build_partition_parser_defaults():
    parser = build_partition_parser()
    args = parser.parse_args(["data.json", "--size", "3"])
    assert args.size == 3
    assert args.json_output is False


def test_main_with_size(tmp_path):
    data = [
        {"label": "a", "runs": [{"elapsed": 1.0, "returncode": 0}]},
        {"label": "b", "runs": [{"elapsed": 2.0, "returncode": 0}]},
    ]
    f = tmp_path / "batches.json"
    f.write_text(json.dumps(data))
    main([str(f), "--size", "1"])


def test_main_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit):
        main([str(tmp_path / "missing.json"), "--size", "2"])
