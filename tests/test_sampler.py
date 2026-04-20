"""Tests for batchmark.sampler."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.sampler import (
    SampledBatch,
    _reservoir,
    _systematic,
    sample_batch,
    sample_all,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_runs(n: int) -> list[RunResult]:
    return [RunResult(elapsed=float(i), returncode=0, stdout="", stderr="") for i in range(n)]


def make_batch(label: str = "cmd", n: int = 20) -> BatchResult:
    runs = make_runs(n)
    return BatchResult(label=label, runs=runs)


# ---------------------------------------------------------------------------
# _reservoir
# ---------------------------------------------------------------------------

def test_reservoir_returns_correct_count():
    runs = make_runs(20)
    result = _reservoir(runs, 5, seed=42)
    assert len(result) == 5


def test_reservoir_all_items_from_source():
    runs = make_runs(20)
    result = _reservoir(runs, 10, seed=0)
    for r in result:
        assert r in runs


def test_reservoir_seed_reproducible():
    runs = make_runs(50)
    a = _reservoir(runs, 10, seed=7)
    b = _reservoir(runs, 10, seed=7)
    assert [r.elapsed for r in a] == [r.elapsed for r in b]


def test_reservoir_different_seeds_differ():
    runs = make_runs(50)
    a = _reservoir(runs, 10, seed=1)
    b = _reservoir(runs, 10, seed=99)
    assert [r.elapsed for r in a] != [r.elapsed for r in b]


# ---------------------------------------------------------------------------
# _systematic
# ---------------------------------------------------------------------------

def test_systematic_returns_correct_count():
    runs = make_runs(20)
    result = _systematic(runs, 5)
    assert len(result) == 5


def test_systematic_returns_all_when_k_exceeds_length():
    runs = make_runs(5)
    result = _systematic(runs, 100)
    assert len(result) == 5


def test_systematic_first_element_is_first_run():
    runs = make_runs(20)
    result = _systematic(runs, 4)
    assert result[0] is runs[0]


# ---------------------------------------------------------------------------
# sample_batch
# ---------------------------------------------------------------------------

def test_sample_batch_returns_sampled_batch():
    batch = make_batch(n=20)
    sb = sample_batch(batch, k=5)
    assert isinstance(sb, SampledBatch)


def test_sample_batch_label_preserved():
    batch = make_batch(label="echo", n=20)
    sb = sample_batch(batch, k=5)
    assert sb.label == "echo"


def test_sample_batch_original_count():
    batch = make_batch(n=20)
    sb = sample_batch(batch, k=5)
    assert sb.original_count == 20


def test_sample_batch_sample_size():
    batch = make_batch(n=20)
    sb = sample_batch(batch, k=7)
    assert sb.sample_size == 7


def test_sample_batch_clamps_k_to_run_count():
    batch = make_batch(n=5)
    sb = sample_batch(batch, k=100)
    assert sb.sample_size == 5


def test_sample_batch_strategy_stored():
    batch = make_batch(n=20)
    sb = sample_batch(batch, k=5, strategy="systematic")
    assert sb.strategy == "systematic"


def test_sample_batch_invalid_strategy_raises():
    batch = make_batch(n=20)
    with pytest.raises(ValueError, match="Unknown strategy"):
        sample_batch(batch, k=5, strategy="random_walk")


# ---------------------------------------------------------------------------
# sample_all
# ---------------------------------------------------------------------------

def test_sample_all_returns_one_per_batch():
    batches = [make_batch(f"cmd{i}", n=20) for i in range(4)]
    results = sample_all(batches, k=5)
    assert len(results) == 4


def test_sample_all_labels_match():
    batches = [make_batch(f"cmd{i}", n=20) for i in range(3)]
    results = sample_all(batches, k=5)
    assert [r.label for r in results] == ["cmd0", "cmd1", "cmd2"]
