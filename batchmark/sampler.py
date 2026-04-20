"""sampler.py — Reservoir and systematic sampling utilities for BatchResult collections."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import BatchResult, RunResult


@dataclass
class SampledBatch:
    label: str
    runs: List[RunResult]
    original_count: int
    sample_size: int
    strategy: str


def _reservoir(runs: List[RunResult], k: int, seed: Optional[int]) -> List[RunResult]:
    """Return k items via reservoir sampling."""
    rng = random.Random(seed)
    reservoir = runs[:k]
    for i in range(k, len(runs)):
        j = rng.randint(0, i)
        if j < k:
            reservoir[j] = runs[i]
    return reservoir


def _systematic(runs: List[RunResult], k: int) -> List[RunResult]:
    """Return k items via systematic (evenly-spaced) sampling."""
    if k >= len(runs):
        return list(runs)
    step = len(runs) / k
    return [runs[int(i * step)] for i in range(k)]


def sample_batch(
    batch: BatchResult,
    k: int,
    strategy: str = "reservoir",
    seed: Optional[int] = None,
) -> SampledBatch:
    """Sample k runs from *batch* using the chosen strategy.

    Parameters
    ----------
    batch:    source BatchResult
    k:        desired sample size (clamped to len(runs))
    strategy: 'reservoir' | 'systematic'
    seed:     optional RNG seed (reservoir only)
    """
    if strategy not in ("reservoir", "systematic"):
        raise ValueError(f"Unknown strategy '{strategy}'. Use 'reservoir' or 'systematic'.")
    runs = batch.runs
    k = max(1, min(k, len(runs)))
    if strategy == "reservoir":
        sampled = _reservoir(runs, k, seed)
    else:
        sampled = _systematic(runs, k)
    return SampledBatch(
        label=batch.label,
        runs=sampled,
        original_count=len(runs),
        sample_size=len(sampled),
        strategy=strategy,
    )


def sample_all(
    batches: List[BatchResult],
    k: int,
    strategy: str = "reservoir",
    seed: Optional[int] = None,
) -> List[SampledBatch]:
    """Apply sample_batch to every BatchResult in *batches*."""
    return [sample_batch(b, k, strategy=strategy, seed=seed) for b in batches]
