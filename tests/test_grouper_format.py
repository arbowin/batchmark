"""Additional formatting and edge-case tests for batchmark.grouper."""

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.grouper import (
    GroupedBatches,
    format_grouped,
    group_by_key,
    group_by_prefix,
)


def make_batch(label: str, n: int = 2) -> BatchResult:
    runs = [RunResult(elapsed=0.05 * i, returncode=0) for i in range(1, n + 1)]
    return BatchResult(label=label, runs=runs)


# --- GroupedBatches helpers ---

def test_grouped_batches_keys_empty():
    gb = GroupedBatches()
    assert gb.keys() == []


def test_grouped_batches_get_missing_key_returns_empty():
    gb = GroupedBatches()
    assert gb.get("nope") == []


def test_grouped_batches_size_reflects_group_count():
    gb = GroupedBatches(groups={"a": [make_batch("a")], "b": [make_batch("b")]})
    assert gb.size() == 2


# --- format_grouped edge cases ---

def test_format_grouped_shows_run_count():
    batches = [make_batch("grp:x", n=5)]
    grouped = group_by_prefix(batches)
    text = format_grouped(grouped)
    assert "runs=5" in text


def test_format_grouped_multiple_groups_all_present():
    batches = [
        make_batch("alpha:one"),
        make_batch("beta:two"),
        make_batch("gamma:three"),
    ]
    grouped = group_by_prefix(batches)
    text = format_grouped(grouped)
    for key in ["alpha", "beta", "gamma"]:
        assert f"[{key}]" in text


def test_format_grouped_single_group_single_batch():
    batches = [make_batch("only")]
    grouped = group_by_label(batches)
    text = format_grouped(grouped)
    assert "[only]" in text
    assert "1 batch" in text


# --- group_by_key with custom function ---

def test_group_by_key_custom_fn_groups_by_run_count():
    batches = [make_batch("a", n=2), make_batch("b", n=2), make_batch("c", n=4)]
    result = group_by_key(batches, lambda b: str(b.total))
    assert "2" in result.keys()
    assert "4" in result.keys()
    assert len(result.get("2")) == 2


def test_group_by_key_all_same_key():
    batches = [make_batch(f"item{i}") for i in range(5)]
    result = group_by_key(batches, lambda _: "same")
    assert result.size() == 1
    assert len(result.get("same")) == 5
