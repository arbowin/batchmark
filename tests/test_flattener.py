"""Tests for batchmark.flattener."""

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.flattener import (
    FlattenedBatch,
    FlattenResult,
    flatten,
    format_flattened,
)


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times, rcs=None) -> BatchResult:
    if rcs is None:
        rcs = [0] * len(times)
    runs = [_run(t, rc) for t, rc in zip(times, rcs)]
    return BatchResult(label=label, runs=runs)


# --- FlattenedBatch helpers ---

def test_flattened_batch_total():
    fb = FlattenedBatch(label="x", runs=[_run(1.0), _run(2.0)])
    assert fb.total() == 2


def test_flattened_batch_success_count_all_ok():
    fb = FlattenedBatch(label="x", runs=[_run(1.0, 0), _run(2.0, 0)])
    assert fb.success_count() == 2


def test_flattened_batch_success_count_partial():
    fb = FlattenedBatch(label="x", runs=[_run(1.0, 0), _run(2.0, 1)])
    assert fb.success_count() == 1


# --- FlattenResult helpers ---

def test_flatten_result_count():
    sources = {"g": [make_batch("a", [1.0, 2.0]), make_batch("b", [3.0])]}
    result = flatten(sources)
    assert result.count() == 2


def test_flatten_result_total_runs():
    sources = {"g": [make_batch("a", [1.0, 2.0]), make_batch("b", [3.0])]}
    result = flatten(sources)
    assert result.total_runs() == 3


def test_flatten_result_labels():
    sources = {"g": [make_batch("a", [1.0]), make_batch("b", [2.0])]}
    result = flatten(sources)
    assert result.labels() == ["a", "b"]


# --- flatten() behaviour ---

def test_flatten_empty_raises():
    with pytest.raises(ValueError):
        flatten({})


def test_flatten_preserves_group_name():
    sources = {"group1": [make_batch("cmd", [1.0])]}
    result = flatten(sources)
    assert result.batches[0].source_group == "group1"


def test_flatten_multiple_groups_no_merge():
    sources = {
        "g1": [make_batch("cmd", [1.0])],
        "g2": [make_batch("cmd", [2.0])],
    }
    result = flatten(sources, merge_same_label=False)
    assert result.count() == 2


def test_flatten_merge_same_label_combines_runs():
    sources = {
        "g1": [make_batch("cmd", [1.0, 2.0])],
        "g2": [make_batch("cmd", [3.0])],
    }
    result = flatten(sources, merge_same_label=True)
    assert result.count() == 1
    assert result.batches[0].total() == 3


def test_flatten_merge_different_labels_stay_separate():
    sources = {
        "g1": [make_batch("a", [1.0])],
        "g2": [make_batch("b", [2.0])],
    }
    result = flatten(sources, merge_same_label=True)
    assert result.count() == 2


# --- format_flattened ---

def test_format_flattened_contains_label():
    sources = {"grp": [make_batch("my-cmd", [1.0, 2.0])]}
    result = flatten(sources)
    text = format_flattened(result)
    assert "my-cmd" in text


def test_format_flattened_contains_run_count():
    sources = {"grp": [make_batch("cmd", [1.0, 2.0, 3.0])]}
    result = flatten(sources)
    text = format_flattened(result)
    assert "3 runs" in text


def test_format_flattened_contains_group():
    sources = {"mygroup": [make_batch("cmd", [1.0])]}
    result = flatten(sources)
    text = format_flattened(result)
    assert "mygroup" in text
