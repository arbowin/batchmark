"""Bootstrap resampling for BatchResult confidence intervals."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import BatchResult
from batchmark.stats import mean, stdev


@dataclass
class ResampleResult:
    label: str
    iterations: int
    mean_ci_low: float
    mean_ci_high: float
    stdev_ci_low: float
    stdev_ci_high: float
    confidence: float
    bootstrap_means: List[float] = field(default_factory=list)


def _bootstrap_means(times: List[float], n: int, seed: Optional[int]) -> List[float]:
    """Generate *n* bootstrap sample means from *times*."""
    rng = random.Random(seed)
    size = len(times)
    results: List[float] = []
    for _ in range(n):
        sample = [rng.choice(times) for _ in range(size)]
        results.append(mean(sample))
    return results


def _bootstrap_stdevs(times: List[float], n: int, seed: Optional[int]) -> List[float]:
    """Generate *n* bootstrap sample standard deviations from *times*."""
    rng = random.Random(seed)
    size = len(times)
    results: List[float] = []
    for _ in range(n):
        sample = [rng.choice(times) for _ in range(size)]
        results.append(stdev(sample))
    return results


def _ci(values: List[float], confidence: float):
    """Return (low, high) percentile bounds for *confidence* level."""
    if not values:
        return 0.0, 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    tail = (1.0 - confidence) / 2.0
    low_idx = max(0, int(tail * n))
    high_idx = min(n - 1, int((1.0 - tail) * n))
    return sorted_vals[low_idx], sorted_vals[high_idx]


def resample(
    batch: BatchResult,
    iterations: int = 1000,
    confidence: float = 0.95,
    seed: Optional[int] = None,
) -> ResampleResult:
    """Bootstrap-resample *batch* and return confidence intervals."""
    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    if not (0.0 < confidence < 1.0):
        raise ValueError("confidence must be between 0 and 1 (exclusive)")

    times = [r.elapsed for r in batch.runs]
    if not times:
        return ResampleResult(
            label=batch.label,
            iterations=iterations,
            mean_ci_low=0.0,
            mean_ci_high=0.0,
            stdev_ci_low=0.0,
            stdev_ci_high=0.0,
            confidence=confidence,
        )

    b_means = _bootstrap_means(times, iterations, seed)
    b_stdevs = _bootstrap_stdevs(times, iterations, seed)

    mean_low, mean_high = _ci(b_means, confidence)
    stdev_low, stdev_high = _ci(b_stdevs, confidence)

    return ResampleResult(
        label=batch.label,
        iterations=iterations,
        mean_ci_low=mean_low,
        mean_ci_high=mean_high,
        stdev_ci_low=stdev_low,
        stdev_ci_high=stdev_high,
        confidence=confidence,
        bootstrap_means=b_means,
    )


def resample_all(
    batches: List[BatchResult],
    iterations: int = 1000,
    confidence: float = 0.95,
    seed: Optional[int] = None,
) -> List[ResampleResult]:
    """Resample every batch in *batches*."""
    return [resample(b, iterations=iterations, confidence=confidence, seed=seed) for b in batches]
