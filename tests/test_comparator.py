"""Tests for batchmark.comparator module."""

import pytest
from batchmark.runner import BatchResult
from batchmark.comparator import compare, format_comparison, ComparisonResult


def make_result(label: str, times, successes: int) -> BatchResult:
    return BatchResult(label=label, times=times, success_count=successes)


def test_compare_ranks_by_mean():
    fast = make_result("fast", [0.1, 0.2, 0.1], 3)
    slow = make_result("slow", [1.0, 1.1, 0.9], 3)
    result = compare([slow, fast])
    assert result.rows[0].label == "fast"
    assert result.rows[0].rank == 1
    assert result.rows[1].rank == 2


def test_compare_winner():
    a = make_result("a", [0.5, 0.5], 2)
    b = make_result("b", [0.3, 0.3], 2)
    result = compare([a, b])
    assert result.winner().label == "b"


def test_compare_success_rate():
    r = make_result("cmd", [0.1, 0.2, 0.3, 0.4], 2)
    result = compare([r])
    assert result.rows[0].success_rate == pytest.approx(50.0)


def test_compare_empty_raises():
    with pytest.raises(ValueError):
        compare([])


def test_compare_default_baseline_is_winner():
    a = make_result("a", [1.0], 1)
    b = make_result("b", [0.5], 1)
    result = compare([a, b])
    assert result.baseline_label == "b"


def test_compare_custom_baseline():
    a = make_result("a", [1.0], 1)
    b = make_result("b", [0.5], 1)
    result = compare([a, b], baseline_label="a")
    assert result.baseline_label == "a"


def test_format_comparison_contains_labels():
    a = make_result("alpha", [0.2, 0.3], 2)
    b = make_result("beta", [0.8, 0.9], 2)
    result = compare([a, b])
    output = format_comparison(result)
    assert "alpha" in output
    assert "beta" in output


def test_format_comparison_contains_winner_line():
    a = make_result("alpha", [0.2, 0.3], 2)
    result = compare([a])
    output = format_comparison(result)
    assert "Winner" in output
    assert "alpha" in output


def test_format_comparison_baseline_marker():
    a = make_result("alpha", [0.2], 1)
    b = make_result("beta", [0.9], 1)
    result = compare([a, b], baseline_label="beta")
    output = format_comparison(result)
    assert "*" in output
