"""Cluster BatchResults by elapsed-time similarity using a simple k-means approach."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from batchmark.runner import BatchResult
from batchmark.stats import mean


@dataclass
class Cluster:
    centroid: float
    members: List[BatchResult] = field(default_factory=list)

    @property
    def labels(self) -> List[str]:
        return [b.label for b in self.members]

    @property
    def size(self) -> int:
        return len(self.members)


@dataclass
class ClusterResult:
    clusters: List[Cluster]

    @property
    def count(self) -> int:
        return len(self.clusters)


def _batch_mean(batch: BatchResult) -> float:
    t = [r.elapsed for r in batch.runs if r.elapsed is not None]
    return mean(t) if t else 0.0


def _assign(batches: List[BatchResult], centroids: List[float]) -> List[Cluster]:
    clusters = [Cluster(centroid=c) for c in centroids]
    for batch in batches:
        bm = _batch_mean(batch)
        closest = min(range(len(centroids)), key=lambda i: abs(centroids[i] - bm))
        clusters[closest].members.append(batch)
    return clusters


def _update_centroids(clusters: List[Cluster]) -> List[float]:
    new_centroids = []
    for cluster in clusters:
        if cluster.members:
            new_centroids.append(mean([_batch_mean(b) for b in cluster.members]))
        else:
            new_centroids.append(cluster.centroid)
    return new_centroids


def clusterize(batches: List[BatchResult], k: int = 3, max_iter: int = 100) -> ClusterResult:
    if not batches:
        raise ValueError("Cannot clusterize empty batch list.")
    if k < 1:
        raise ValueError("k must be at least 1.")
    k = min(k, len(batches))
    sorted_means = sorted(batches, key=_batch_mean)
    step = max(1, len(sorted_means) // k)
    centroids = [_batch_mean(sorted_means[i * step]) for i in range(k)]
    clusters: List[Cluster] = []
    for _ in range(max_iter):
        clusters = _assign(batches, centroids)
        new_centroids = _update_centroids(clusters)
        if new_centroids == centroids:
            break
        centroids = new_centroids
    return ClusterResult(clusters=clusters)


def format_clusters(result: ClusterResult) -> str:
    lines = ["Cluster Summary", "=" * 40]
    for i, cluster in enumerate(result.clusters):
        lines.append(f"Cluster {i + 1}  centroid={cluster.centroid:.4f}s  members={cluster.size}")
        for label in cluster.labels:
            lines.append(f"  - {label}")
    return "\n".join(lines)
