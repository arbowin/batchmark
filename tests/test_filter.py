"""Tests for batchmark.filter module."""

import pytest
from batchmark.runner import BatchResult
from batchmark.filter import (
    FilterCriteria,
    filter_results,
    success_rate,
    top_n,
)


def make_result(label, times, success_count):
    return BatchResult(label=label, times=times, success_count=success_count)


def test_success_rate_full():
    r = make_result("a", [0.1, 0.2, 0.3], 3)
    assert success_rate(r) == 1.0


def test_success_rate_partial():
    r = make_result("a", [0.1, 0.2, 0.3, 0.4], 2)
    assert success_rate(r) == 0.5


def test_success_rate_empty():
    r = make_result("a", [], 0)
    assert success_rate(r) == 0.0


def test_filter_by_min_success_rate():
    results = [
        make_result("good", [0.1, 0.2], 2),
        make_result("bad", [0.1, 0.2], 0),
    ]
    criteria = FilterCriteria(min_success_rate=0.9)
    out = filter_results(results, criteria)
    assert len(out) == 1
    assert out[0].label == "good"


def test_filter_by_max_mean_time():
    results = [
        make_result("fast", [0.1, 0.1], 2),
        make_result("slow", [1.0, 2.0], 2),
    ]
    criteria = FilterCriteria(max_mean_time=0.5)
    out = filter_results(results, criteria)
    assert len(out) == 1
    assert out[0].label == "fast"


def test_filter_by_min_iterations():
    results = [
        make_result("few", [0.1], 1),
        make_result("many", [0.1, 0.2, 0.3], 3),
    ]
    criteria = FilterCriteria(min_iterations=3)
    out = filter_results(results, criteria)
    assert len(out) == 1
    assert out[0].label == "many"


def test_filter_by_label_contains():
    results = [
        make_result("grep test", [0.1], 1),
        make_result("ls -la", [0.2], 1),
    ]
    criteria = FilterCriteria(label_contains="grep")
    out = filter_results(results, criteria)
    assert len(out) == 1
    assert "grep" in out[0].label


def test_filter_no_criteria_returns_all():
    results = [make_result(str(i), [0.1 * i], i) for i in range(1, 5)]
    out = filter_results(results, FilterCriteria())
    assert len(out) == 4


def test_top_n_returns_fastest():
    results = [
        make_result("slow", [1.0, 1.5], 2),
        make_result("fast", [0.1, 0.2], 2),
        make_result("mid", [0.5, 0.6], 2),
    ]
    out = top_n(results, 2)
    assert out[0].label == "fast"
    assert out[1].label == "mid"


def test_top_n_empty():
    assert top_n([], 3) == []
