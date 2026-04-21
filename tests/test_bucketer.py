"""Tests for batchmark.bucketer."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.bucketer import (
    Bucket,
    BucketResult,
    bucket_batch,
    bucket_all,
    format_bucket_result,
)


def make_batch(label: str, elapsed_list, successes=None) -> BatchResult:
    if successes is None:
        successes = [True] * len(elapsed_list)
    runs = [
        RunResult(elapsed=e, success=s, stdout="", stderr="", returncode=0 if s else 1)
        for e, s in zip(elapsed_list, successes)
    ]
    return BatchResult(label=label, runs=runs)


def test_bucket_batch_correct_bucket_count():
    batch = make_batch("cmd", [0.1] * 10)
    result = bucket_batch(batch, bucket_size=3)
    # 10 runs with size 3 => buckets of 3,3,3,1 = 4 buckets
    assert result.bucket_count() == 4


def test_bucket_batch_run_counts():
    batch = make_batch("cmd", [0.1] * 7)
    result = bucket_batch(batch, bucket_size=4)
    assert result.buckets[0].run_count() == 4
    assert result.buckets[1].run_count() == 3


def test_bucket_batch_label_preserved():
    batch = make_batch("my-cmd", [0.2, 0.3])
    result = bucket_batch(batch, bucket_size=2)
    assert result.label == "my-cmd"
    assert result.buckets[0].label == "my-cmd"


def test_bucket_batch_invalid_size_raises():
    batch = make_batch("cmd", [0.1])
    with pytest.raises(ValueError):
        bucket_batch(batch, bucket_size=0)


def test_bucket_mean_correct():
    batch = make_batch("cmd", [0.2, 0.4, 0.6])
    result = bucket_batch(batch, bucket_size=3)
    assert abs(result.buckets[0].mean() - 0.4) < 1e-9


def test_bucket_success_rate_partial():
    batch = make_batch("cmd", [0.1, 0.2, 0.3], successes=[True, False, True])
    result = bucket_batch(batch, bucket_size=3)
    assert abs(result.buckets[0].success_rate() - 2 / 3) < 1e-9


def test_bucket_best_and_worst():
    batch = make_batch("cmd", [0.5, 0.5, 0.1, 0.1, 0.9, 0.9])
    result = bucket_batch(batch, bucket_size=2)
    best = result.best_bucket()
    worst = result.worst_bucket()
    assert best is not None and abs(best.mean() - 0.1) < 1e-9
    assert worst is not None and abs(worst.mean() - 0.9) < 1e-9


def test_bucket_all_keys_match_labels():
    b1 = make_batch("alpha", [0.1, 0.2])
    b2 = make_batch("beta", [0.3, 0.4])
    results = bucket_all([b1, b2], bucket_size=1)
    assert set(results.keys()) == {"alpha", "beta"}


def test_bucket_all_each_result_correct_size():
    b1 = make_batch("alpha", [0.1] * 5)
    results = bucket_all([b1], bucket_size=2)
    assert results["alpha"].bucket_count() == 3


def test_format_bucket_result_contains_label():
    batch = make_batch("my-tool", [0.1, 0.2])
    result = bucket_batch(batch, bucket_size=1)
    output = format_bucket_result(result)
    assert "my-tool" in output


def test_format_bucket_result_contains_bucket_index():
    batch = make_batch("cmd", [0.1, 0.2, 0.3])
    result = bucket_batch(batch, bucket_size=1)
    output = format_bucket_result(result)
    assert "Bucket" in output
    assert "0" in output
