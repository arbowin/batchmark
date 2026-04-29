"""Tests for batchmark.reducer."""
import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.reducer import (
    ReducedBatch,
    ReduceResult,
    reduce,
    format_reduced,
)


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def _batch(label: str, *elapseds: float, rc: int = 0) -> BatchResult:
    return BatchResult(label=label, runs=[_run(e, rc) for e in elapseds])


# ---------------------------------------------------------------------------
# reduce – basic behaviour
# ---------------------------------------------------------------------------

def test_reduce_empty_sources_raises():
    with pytest.raises(ValueError):
        reduce([])


def test_reduce_single_source_single_batch_mean():
    source = [_batch("cmd", 1.0, 2.0, 3.0)]
    result = reduce([source], strategy="mean")
    assert result.count() == 1
    assert result.batches[0].runs[0].elapsed == pytest.approx(2.0)


def test_reduce_single_source_single_batch_median():
    source = [_batch("cmd", 1.0, 2.0, 9.0)]
    result = reduce([source], strategy="median")
    assert result.batches[0].runs[0].elapsed == pytest.approx(2.0)


def test_reduce_multiple_sources_averages_across_sources():
    s1 = [_batch("cmd", 2.0)]
    s2 = [_batch("cmd", 4.0)]
    result = reduce([s1, s2], strategy="mean")
    assert result.batches[0].runs[0].elapsed == pytest.approx(3.0)


def test_reduce_source_count_tracked():
    s1 = [_batch("cmd", 1.0)]
    s2 = [_batch("cmd", 2.0)]
    s3 = [_batch("cmd", 3.0)]
    result = reduce([s1, s2, s3])
    assert result.batches[0].source_count == 3


def test_reduce_separate_labels_kept_separate():
    source = [_batch("a", 1.0), _batch("b", 2.0)]
    result = reduce([source])
    assert set(result.labels()) == {"a", "b"}


def test_reduce_strategy_stored_on_batch():
    source = [_batch("cmd", 1.0)]
    result = reduce([source], strategy="median")
    assert result.batches[0].strategy == "median"


def test_reduce_returncode_majority_success():
    # 2 successes, 1 failure → success
    s1 = [_batch("cmd", 1.0, rc=0)]
    s2 = [_batch("cmd", 1.0, rc=0)]
    s3 = [_batch("cmd", 1.0, rc=1)]
    result = reduce([s1, s2, s3])
    assert result.batches[0].runs[0].returncode == 0


def test_reduce_returncode_majority_failure():
    s1 = [_batch("cmd", 1.0, rc=1)]
    s2 = [_batch("cmd", 1.0, rc=1)]
    s3 = [_batch("cmd", 1.0, rc=0)]
    result = reduce([s1, s2, s3])
    assert result.batches[0].runs[0].returncode == 1


# ---------------------------------------------------------------------------
# ReducedBatch helpers
# ---------------------------------------------------------------------------

def test_reduced_batch_total():
    rb = ReducedBatch(label="x", runs=[_run(1.0), _run(2.0)], strategy="mean", source_count=1)
    assert rb.total() == 2


def test_reduced_batch_success_count():
    rb = ReducedBatch(
        label="x",
        runs=[_run(1.0, 0), _run(2.0, 1), _run(3.0, 0)],
        strategy="mean",
        source_count=1,
    )
    assert rb.success_count() == 2


# ---------------------------------------------------------------------------
# format_reduced
# ---------------------------------------------------------------------------

def test_format_reduced_contains_label():
    source = [_batch("myjob", 1.5)]
    result = reduce([source])
    output = format_reduced(result)
    assert "myjob" in output


def test_format_reduced_contains_strategy():
    source = [_batch("job", 1.0)]
    result = reduce([source], strategy="median")
    output = format_reduced(result)
    assert "median" in output


def test_format_reduced_contains_source_count():
    s1 = [_batch("job", 1.0)]
    s2 = [_batch("job", 2.0)]
    result = reduce([s1, s2])
    output = format_reduced(result)
    assert "sources=2" in output
