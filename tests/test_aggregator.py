"""Tests for batchmark.aggregator."""

import pytest
from batchmark.runner import BatchResult, RunResult
from batchmark.aggregator import AggregatedResult, aggregate, format_aggregated


def make_batch(label: str, times, successes=None):
    results = []
    for i, t in enumerate(times):
        ok = successes[i] if successes else True
        results.append(RunResult(command="echo x", elapsed=t, returncode=0 if ok else 1, success=ok))
    return BatchResult(label=label, results=results)


def test_aggregate_single_batch():
    batch = make_batch("cmd", [0.1, 0.2, 0.3])
    result = aggregate([batch])
    assert len(result) == 1
    assert result[0].label == "cmd"
    assert result[0].total_runs == 3
    assert result[0].total_successes == 3


def test_aggregate_merges_same_label():
    b1 = make_batch("cmd", [0.1, 0.2])
    b2 = make_batch("cmd", [0.3, 0.4])
    result = aggregate([b1, b2])
    assert len(result) == 1
    assert result[0].total_runs == 4
    assert len(result[0].all_times) == 4


def test_aggregate_separate_labels():
    b1 = make_batch("a", [0.1])
    b2 = make_batch("b", [0.2])
    result = aggregate([b1, b2])
    labels = {r.label for r in result}
    assert labels == {"a", "b"}


def test_aggregate_success_rate_partial():
    batch = make_batch("cmd", [0.1, 0.2, 0.3], successes=[True, False, True])
    result = aggregate([batch])
    assert pytest.approx(result[0].success_rate, 0.01) == 2 / 3


def test_aggregate_empty_raises():
    with pytest.raises(ValueError):
        aggregate([])


def test_aggregate_summary_keys():
    batch = make_batch("cmd", [0.1, 0.2, 0.3])
    result = aggregate([batch])
    summary = result[0].summary
    assert "mean" in summary
    assert "median" in summary
    assert "stdev" in summary


def test_aggregate_empty_times_summary():
    batch = make_batch("cmd", [])
    result = aggregate([batch])
    assert result[0].summary == {}


def test_format_aggregated_contains_label():
    batch = make_batch("mycmd", [0.1, 0.2])
    result = aggregate([batch])
    output = format_aggregated(result)
    assert "mycmd" in output


def test_format_aggregated_contains_header():
    batch = make_batch("x", [0.5])
    result = aggregate([batch])
    output = format_aggregated(result)
    assert "Aggregated" in output


def test_format_aggregated_multiple():
    b1 = make_batch("alpha", [0.1])
    b2 = make_batch("beta", [0.2])
    output = format_aggregated(aggregate([b1, b2]))
    assert "alpha" in output and "beta" in output
