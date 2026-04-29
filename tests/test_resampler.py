"""Tests for batchmark.resampler."""
import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.resampler import (
    ResampleResult,
    _bootstrap_means,
    _ci,
    resample,
    resample_all,
)


def _run(elapsed: float, returncode: int = 0) -> RunResult:
    return RunResult(command="echo hi", elapsed=elapsed, returncode=returncode, stdout="", stderr="")


def make_batch(label: str, times, returncode: int = 0) -> BatchResult:
    runs = [_run(t, returncode) for t in times]
    return BatchResult(label=label, runs=runs)


# --- _bootstrap_means ---

def test_bootstrap_means_count():
    result = _bootstrap_means([1.0, 2.0, 3.0], n=200, seed=42)
    assert len(result) == 200


def test_bootstrap_means_seed_reproducible():
    a = _bootstrap_means([1.0, 2.0, 3.0, 4.0], n=100, seed=7)
    b = _bootstrap_means([1.0, 2.0, 3.0, 4.0], n=100, seed=7)
    assert a == b


def test_bootstrap_means_different_seeds_differ():
    a = _bootstrap_means([1.0, 2.0, 3.0, 4.0], n=100, seed=1)
    b = _bootstrap_means([1.0, 2.0, 3.0, 4.0], n=100, seed=99)
    assert a != b


# --- _ci ---

def test_ci_empty_returns_zeros():
    assert _ci([], 0.95) == (0.0, 0.0)


def test_ci_low_less_than_high():
    values = list(range(1, 101))
    low, high = _ci(values, 0.95)
    assert low < high


def test_ci_full_confidence_covers_all():
    values = [float(i) for i in range(1, 11)]
    low, high = _ci(values, 0.9999)
    assert low <= min(values)
    assert high >= max(values) * 0.9  # near max


# --- resample ---

def test_resample_returns_resample_result():
    batch = make_batch("cmd", [0.1, 0.2, 0.3, 0.15, 0.25])
    result = resample(batch, iterations=500, seed=0)
    assert isinstance(result, ResampleResult)


def test_resample_label_preserved():
    batch = make_batch("my_label", [0.1, 0.2, 0.3])
    result = resample(batch, iterations=100, seed=1)
    assert result.label == "my_label"


def test_resample_ci_low_le_high():
    batch = make_batch("cmd", [0.05, 0.10, 0.15, 0.20, 0.25])
    result = resample(batch, iterations=500, seed=42)
    assert result.mean_ci_low <= result.mean_ci_high
    assert result.stdev_ci_low <= result.stdev_ci_high


def test_resample_bootstrap_means_length():
    batch = make_batch("cmd", [1.0, 2.0, 3.0])
    result = resample(batch, iterations=300, seed=5)
    assert len(result.bootstrap_means) == 300


def test_resample_empty_batch_returns_zeros():
    batch = BatchResult(label="empty", runs=[])
    result = resample(batch, iterations=100, seed=0)
    assert result.mean_ci_low == 0.0
    assert result.mean_ci_high == 0.0


def test_resample_invalid_iterations_raises():
    batch = make_batch("cmd", [0.1, 0.2])
    with pytest.raises(ValueError, match="iterations"):
        resample(batch, iterations=0)


def test_resample_invalid_confidence_raises():
    batch = make_batch("cmd", [0.1, 0.2])
    with pytest.raises(ValueError, match="confidence"):
        resample(batch, confidence=1.5)


def test_resample_confidence_stored():
    batch = make_batch("cmd", [0.1, 0.2, 0.3])
    result = resample(batch, confidence=0.90, seed=0)
    assert result.confidence == 0.90


# --- resample_all ---

def test_resample_all_returns_one_per_batch():
    batches = [make_batch(f"cmd{i}", [0.1 * i, 0.2 * i, 0.3 * i]) for i in range(1, 5)]
    results = resample_all(batches, iterations=100, seed=0)
    assert len(results) == 4


def test_resample_all_labels_match():
    batches = [make_batch("alpha", [0.1, 0.2]), make_batch("beta", [0.3, 0.4])]
    results = resample_all(batches, iterations=100, seed=0)
    assert [r.label for r in results] == ["alpha", "beta"]
