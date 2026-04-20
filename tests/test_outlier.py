"""Tests for batchmark.outlier module."""

import pytest
from batchmark.runner import RunResult, BatchResult
from batchmark.outlier import (
    OutlierResult,
    detect_outliers,
    format_outlier_report,
    _iqr_bounds,
    _zscore_bounds,
)


def make_batch(label: str, elapsed_times: list) -> BatchResult:
    runs = [
        RunResult(command="echo test", elapsed=t, returncode=0, stdout="", stderr="")
        for t in elapsed_times
    ]
    return BatchResult(label=label, runs=runs)


# --- _iqr_bounds ---

def test_iqr_bounds_returns_tuple():
    low, high = _iqr_bounds([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    assert isinstance(low, float)
    assert isinstance(high, float)
    assert low < high


def test_iqr_bounds_outlier_outside_range():
    times = [1.0, 1.1, 1.0, 1.2, 1.1, 1.0, 1.1, 50.0]
    low, high = _iqr_bounds(times)
    assert 50.0 > high


# --- _zscore_bounds ---

def test_zscore_bounds_symmetric():
    times = [1.0, 2.0, 3.0, 4.0, 5.0]
    low, high = _zscore_bounds(times, z=2.5)
    m = sum(times) / len(times)
    assert abs((high - m) - (m - low)) < 1e-9


def test_zscore_bounds_constant_returns_inf():
    low, high = _zscore_bounds([1.0, 1.0, 1.0, 1.0])
    assert low == float("-inf")
    assert high == float("inf")


def test_zscore_bounds_too_few_points():
    low, high = _zscore_bounds([1.0])
    assert low == float("-inf")
    assert high == float("inf")


# --- detect_outliers ---

def test_detect_outliers_returns_none_for_small_sample():
    batch = make_batch("tiny", [1.0, 2.0, 3.0])
    assert detect_outliers(batch) is None


def test_detect_outliers_no_outliers():
    times = [1.0, 1.05, 1.02, 1.03, 1.01, 1.04, 1.02, 1.03]
    batch = make_batch("stable", times)
    result = detect_outliers(batch)
    assert result is not None
    assert not result.has_outliers


def test_detect_outliers_finds_spike():
    times = [1.0, 1.05, 1.02, 1.03, 1.01, 1.04, 1.02, 99.0]
    batch = make_batch("spiky", times)
    result = detect_outliers(batch)
    assert result is not None
    assert result.has_outliers
    assert 99.0 in result.outliers


def test_detect_outliers_clean_excludes_outlier():
    times = [1.0, 1.05, 1.02, 1.03, 1.01, 1.04, 1.02, 99.0]
    batch = make_batch("spiky", times)
    result = detect_outliers(batch)
    assert 99.0 not in result.clean


def test_detect_outliers_zscore_method():
    times = [1.0, 1.05, 1.02, 1.03, 1.01, 1.04, 1.02, 50.0]
    batch = make_batch("zscore", times)
    result = detect_outliers(batch, method="zscore", z_threshold=2.0)
    assert result is not None
    assert result.has_outliers


def test_detect_outliers_label_preserved():
    batch = make_batch("my-cmd", [1.0, 1.1, 1.0, 1.2, 1.1, 1.0, 1.1, 1.05])
    result = detect_outliers(batch)
    assert result.label == "my-cmd"


def test_detect_outliers_outlier_count():
    times = [1.0] * 7 + [100.0, 200.0]
    batch = make_batch("multi", times)
    result = detect_outliers(batch)
    assert result.outlier_count == 2


# --- format_outlier_report ---

def test_format_outlier_report_contains_label():
    times = [1.0, 1.05, 1.02, 1.03, 1.01, 1.04, 1.02, 99.0]
    batch = make_batch("my-label", times)
    result = detect_outliers(batch)
    report = format_outlier_report(result)
    assert "my-label" in report


def test_format_outlier_report_no_outliers_message():
    times = [1.0, 1.05, 1.02, 1.03, 1.01, 1.04, 1.02, 1.03]
    batch = make_batch("clean", times)
    result = detect_outliers(batch)
    report = format_outlier_report(result)
    assert "No outliers detected" in report


def test_format_outlier_report_shows_outlier_values():
    times = [1.0] * 7 + [99.0]
    batch = make_batch("spiky", times)
    result = detect_outliers(batch)
    report = format_outlier_report(result)
    assert "99.0000s" in report
