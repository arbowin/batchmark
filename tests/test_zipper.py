"""Tests for batchmark.zipper."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.zipper import ZipResult, ZippedPair, format_zip, zip_batches


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times, rcs=None) -> BatchResult:
    if rcs is None:
        rcs = [0] * len(times)
    runs = [_run(t, rc) for t, rc in zip(times, rcs)]
    return BatchResult(label=label, runs=runs)


# ---------------------------------------------------------------------------
# zip_batches
# ---------------------------------------------------------------------------

def test_zip_returns_zip_result():
    left = [make_batch("a", [1.0, 2.0])]
    right = [make_batch("a", [1.5, 2.5])]
    result = zip_batches(left, right)
    assert isinstance(result, ZipResult)


def test_zip_common_label_creates_pair():
    left = [make_batch("a", [1.0, 2.0])]
    right = [make_batch("a", [3.0, 4.0])]
    result = zip_batches(left, right)
    assert result.count == 1
    assert result.pairs[0].label == "a"


def test_zip_left_mean_correct():
    left = [make_batch("x", [2.0, 4.0])]
    right = [make_batch("x", [1.0])]
    result = zip_batches(left, right)
    assert result.pairs[0].left_mean == pytest.approx(3.0)


def test_zip_right_mean_correct():
    left = [make_batch("x", [1.0])]
    right = [make_batch("x", [2.0, 6.0])]
    result = zip_batches(left, right)
    assert result.pairs[0].right_mean == pytest.approx(4.0)


def test_zip_delta_is_right_minus_left():
    left = [make_batch("x", [1.0])]
    right = [make_batch("x", [3.0])]
    result = zip_batches(left, right)
    assert result.pairs[0].delta == pytest.approx(2.0)


def test_zip_ratio_correct():
    left = [make_batch("x", [2.0])]
    right = [make_batch("x", [4.0])]
    result = zip_batches(left, right)
    assert result.pairs[0].ratio == pytest.approx(2.0)


def test_zip_ratio_none_when_left_mean_zero():
    left = [make_batch("x", [0.0])]
    right = [make_batch("x", [1.0])]
    result = zip_batches(left, right)
    assert result.pairs[0].ratio is None


def test_zip_left_only_recorded():
    left = [make_batch("a", [1.0]), make_batch("b", [1.0])]
    right = [make_batch("a", [1.0])]
    result = zip_batches(left, right)
    assert "b" in result.left_only


def test_zip_right_only_recorded():
    left = [make_batch("a", [1.0])]
    right = [make_batch("a", [1.0]), make_batch("c", [1.0])]
    result = zip_batches(left, right)
    assert "c" in result.right_only


def test_zip_no_common_labels_empty_pairs():
    left = [make_batch("a", [1.0])]
    right = [make_batch("b", [1.0])]
    result = zip_batches(left, right)
    assert result.count == 0
    assert "a" in result.left_only
    assert "b" in result.right_only


def test_zip_success_counts():
    left = [make_batch("a", [1.0, 1.0, 1.0], [0, 0, 1])]
    right = [make_batch("a", [1.0, 1.0], [0, 1])]
    result = zip_batches(left, right)
    p = result.pairs[0]
    assert p.left_success == 2
    assert p.right_success == 1


def test_zip_totals():
    left = [make_batch("a", [1.0, 2.0, 3.0])]
    right = [make_batch("a", [1.0, 2.0])]
    result = zip_batches(left, right)
    p = result.pairs[0]
    assert p.left_total == 3
    assert p.right_total == 2


# ---------------------------------------------------------------------------
# format_zip
# ---------------------------------------------------------------------------

def test_format_zip_contains_label():
    left = [make_batch("my_cmd", [1.0])]
    right = [make_batch("my_cmd", [2.0])]
    result = zip_batches(left, right)
    text = format_zip(result)
    assert "my_cmd" in text


def test_format_zip_no_common_message():
    result = ZipResult(pairs=[], left_only=[], right_only=[])
    text = format_zip(result)
    assert "No common" in text


def test_format_zip_custom_names_in_header():
    left = [make_batch("a", [1.0])]
    right = [make_batch("a", [2.0])]
    result = zip_batches(left, right)
    text = format_zip(result, left_name="baseline", right_name="candidate")
    assert "baseline" in text
    assert "candidate" in text


def test_format_zip_shows_left_only():
    left = [make_batch("a", [1.0]), make_batch("b", [1.0])]
    right = [make_batch("a", [1.0])]
    result = zip_batches(left, right)
    text = format_zip(result)
    assert "b" in text
