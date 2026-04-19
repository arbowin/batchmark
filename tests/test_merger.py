"""Tests for batchmark.merger."""

import pytest
from batchmark.runner import BatchResult, RunResult
from batchmark.merger import merge, format_merge_summary, MergeResult


def make_run(elapsed: float, success: bool = True) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=0 if success else 1, success=success)


def make_batch(label: str, times, successes=None) -> BatchResult:
    if successes is None:
        successes = [True] * len(times)
    runs = [make_run(t, s) for t, s in zip(times, successes)]
    return BatchResult(label=label, runs=runs)


def test_merge_empty_raises():
    with pytest.raises(ValueError):
        merge([])


def test_merge_single_source_single_batch():
    batch = make_batch("cmd_a", [1.0, 2.0])
    result = merge([("src1", [batch])])
    assert len(result.batches) == 1
    assert result.batches[0].label == "cmd_a"


def test_merge_combines_runs_same_label():
    b1 = make_batch("cmd_a", [1.0, 2.0])
    b2 = make_batch("cmd_a", [3.0, 4.0])
    result = merge([("src1", [b1]), ("src2", [b2])])
    merged = result.get("cmd_a")
    assert merged is not None
    assert len(merged.runs) == 4


def test_merge_separate_labels():
    b1 = make_batch("cmd_a", [1.0])
    b2 = make_batch("cmd_b", [2.0])
    result = merge([("src1", [b1, b2])])
    assert set(result.labels()) == {"cmd_a", "cmd_b"}


def test_merge_tracks_sources():
    b1 = make_batch("cmd_a", [1.0])
    b2 = make_batch("cmd_a", [2.0])
    result = merge([("alpha", [b1]), ("beta", [b2])])
    merged = result.get("cmd_a")
    assert "alpha" in merged.sources
    assert "beta" in merged.sources


def test_merge_deduplicates_source_names():
    b1 = make_batch("cmd_a", [1.0])
    b2 = make_batch("cmd_a", [2.0])
    result = merge([("src1", [b1]), ("src1", [b2])])
    merged = result.get("cmd_a")
    assert merged.sources.count("src1") == 1


def test_merge_success_count():
    batch = make_batch("cmd_a", [1.0, 2.0, 3.0], [True, False, True])
    result = merge([("src1", [batch])])
    merged = result.get("cmd_a")
    assert merged.success_count == 2
    assert merged.total == 3


def test_merge_times_excludes_failures():
    batch = make_batch("cmd_a", [1.0, 2.0], [True, False])
    result = merge([("src1", [batch])])
    merged = result.get("cmd_a")
    assert merged.times == [1.0]


def test_format_merge_summary_contains_label():
    batch = make_batch("my_cmd", [1.0, 2.0])
    result = merge([("src1", [batch])])
    output = format_merge_summary(result)
    assert "my_cmd" in output


def test_format_merge_summary_contains_sources():
    batch = make_batch("cmd_a", [1.0])
    result = merge([("origin", [batch])])
    output = format_merge_summary(result)
    assert "origin" in output
