"""Tests for batchmark.clusterizer."""

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.clusterizer import (
    Cluster,
    ClusterResult,
    _batch_mean,
    clusterize,
    format_clusters,
)


def make_batch(label: str, times: list) -> BatchResult:
    runs = [RunResult(elapsed=t, returncode=0, stdout="", stderr="") for t in times]
    return BatchResult(label=label, runs=runs)


def test_batch_mean_basic():
    b = make_batch("a", [1.0, 2.0, 3.0])
    assert _batch_mean(b) == pytest.approx(2.0)


def test_batch_mean_empty():
    b = BatchResult(label="empty", runs=[])
    assert _batch_mean(b) == 0.0


def test_clusterize_returns_cluster_result():
    batches = [make_batch(f"cmd{i}", [float(i)]) for i in range(6)]
    result = clusterize(batches, k=2)
    assert isinstance(result, ClusterResult)


def test_clusterize_correct_k():
    batches = [make_batch(f"cmd{i}", [float(i)]) for i in range(6)]
    result = clusterize(batches, k=3)
    assert result.count == 3


def test_clusterize_all_members_assigned():
    batches = [make_batch(f"cmd{i}", [float(i)]) for i in range(9)]
    result = clusterize(batches, k=3)
    total = sum(c.size for c in result.clusters)
    assert total == len(batches)


def test_clusterize_separates_fast_and_slow():
    fast = [make_batch(f"fast{i}", [0.01 + i * 0.001]) for i in range(3)]
    slow = [make_batch(f"slow{i}", [10.0 + i * 0.1]) for i in range(3)]
    result = clusterize(fast + slow, k=2)
    centroids = sorted(c.centroid for c in result.clusters)
    assert centroids[0] < 1.0
    assert centroids[1] > 5.0


def test_clusterize_k_larger_than_batches_clips():
    batches = [make_batch("only", [1.0])]
    result = clusterize(batches, k=5)
    assert result.count == 1


def test_clusterize_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        clusterize([], k=2)


def test_clusterize_k_zero_raises():
    batches = [make_batch("a", [1.0])]
    with pytest.raises(ValueError, match="k must be"):
        clusterize(batches, k=0)


def test_cluster_labels():
    b1 = make_batch("alpha", [1.0])
    b2 = make_batch("beta", [1.1])
    c = Cluster(centroid=1.05, members=[b1, b2])
    assert "alpha" in c.labels
    assert "beta" in c.labels


def test_format_clusters_contains_header():
    batches = [make_batch(f"cmd{i}", [float(i)]) for i in range(4)]
    result = clusterize(batches, k=2)
    text = format_clusters(result)
    assert "Cluster Summary" in text


def test_format_clusters_contains_labels():
    batches = [make_batch("mycommand", [1.0])]
    result = clusterize(batches, k=1)
    text = format_clusters(result)
    assert "mycommand" in text


def test_format_clusters_shows_centroid():
    batches = [make_batch("x", [2.5])]
    result = clusterize(batches, k=1)
    text = format_clusters(result)
    assert "centroid=" in text
