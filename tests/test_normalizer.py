"""Tests for batchmark.normalizer."""

import pytest
from batchmark.runner import RunResult, BatchResult
from batchmark.normalizer import (
    normalize,
    format_normalization,
    NormalizationResult,
    NormalizedEntry,
)


def make_batch(label: str, times: list, failures: int = 0) -> BatchResult:
    runs = [RunResult(elapsed=t, success=True, stdout="", stderr="") for t in times]
    runs += [RunResult(elapsed=0.0, success=False, stdout="", stderr="err") for _ in range(failures)]
    return BatchResult(label=label, runs=runs)


def test_normalize_baseline_entry_has_score_one():
    batches = [make_batch("base", [1.0, 1.0, 1.0])]
    result = normalize(batches, baseline_label="base")
    entry = next(e for e in result.entries if e.label == "base")
    assert entry.normalized_score == pytest.approx(1.0)


def test_normalize_faster_batch_score_less_than_one():
    batches = [
        make_batch("base", [2.0, 2.0]),
        make_batch("fast", [1.0, 1.0]),
    ]
    result = normalize(batches, baseline_label="base")
    fast_entry = next(e for e in result.entries if e.label == "fast")
    assert fast_entry.normalized_score == pytest.approx(0.5)


def test_normalize_slower_batch_score_greater_than_one():
    batches = [
        make_batch("base", [1.0, 1.0]),
        make_batch("slow", [3.0, 3.0]),
    ]
    result = normalize(batches, baseline_label="base")
    slow_entry = next(e for e in result.entries if e.label == "slow")
    assert slow_entry.normalized_score == pytest.approx(3.0)


def test_normalize_speedup_is_inverse_of_normalized_score():
    batches = [
        make_batch("base", [2.0, 2.0]),
        make_batch("fast", [1.0, 1.0]),
    ]
    result = normalize(batches, baseline_label="base")
    fast_entry = next(e for e in result.entries if e.label == "fast")
    assert fast_entry.speedup == pytest.approx(2.0)


def test_normalize_entries_sorted_by_score():
    batches = [
        make_batch("base", [2.0, 2.0]),
        make_batch("slow", [4.0, 4.0]),
        make_batch("fast", [1.0, 1.0]),
    ]
    result = normalize(batches, baseline_label="base")
    scores = [e.normalized_score for e in result.entries]
    assert scores == sorted(scores)


def test_normalize_missing_baseline_raises():
    batches = [make_batch("only", [1.0])]
    with pytest.raises(ValueError, match="Baseline label"):
        normalize(batches, baseline_label="missing")


def test_normalize_empty_batches_raises():
    with pytest.raises(ValueError, match="No batches"):
        normalize([], baseline_label="base")


def test_normalize_baseline_zero_mean_raises():
    batches = [make_batch("base", [], failures=2)]
    with pytest.raises(ValueError, match="zero or undefined"):
        normalize(batches, baseline_label="base")


def test_fastest_returns_min_score():
    batches = [
        make_batch("base", [2.0]),
        make_batch("fast", [0.5]),
        make_batch("slow", [5.0]),
    ]
    result = normalize(batches, baseline_label="base")
    assert result.fastest().label == "fast"


def test_slowest_returns_max_score():
    batches = [
        make_batch("base", [2.0]),
        make_batch("fast", [0.5]),
        make_batch("slow", [5.0]),
    ]
    result = normalize(batches, baseline_label="base")
    assert result.slowest().label == "slow"


def test_format_normalization_contains_baseline_label():
    batches = [make_batch("base", [1.0, 2.0])]
    result = normalize(batches, baseline_label="base")
    output = format_normalization(result)
    assert "base" in output


def test_format_normalization_contains_header():
    batches = [make_batch("base", [1.0])]
    result = normalize(batches, baseline_label="base")
    output = format_normalization(result)
    assert "Normalized" in output
    assert "Speedup" in output
