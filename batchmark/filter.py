"""Filter and select BatchResults based on criteria."""

from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BatchResult


@dataclass
class FilterCriteria:
    min_success_rate: float = 0.0
    max_mean_time: Optional[float] = None
    min_iterations: int = 1
    label_contains: Optional[str] = None


def success_rate(result: BatchResult) -> float:
    """Return success rate as a float between 0 and 1."""
    total = len(result.times)
    if total == 0:
        return 0.0
    return result.success_count / total


def filter_results(
    results: List[BatchResult],
    criteria: FilterCriteria,
) -> List[BatchResult]:
    """Return only results matching all criteria."""
    filtered = []
    for r in results:
        if len(r.times) < criteria.min_iterations:
            continue
        if success_rate(r) < criteria.min_success_rate:
            continue
        if criteria.max_mean_time is not None:
            mean_t = sum(r.times) / len(r.times) if r.times else float("inf")
            if mean_t > criteria.max_mean_time:
                continue
        if criteria.label_contains is not None:
            if criteria.label_contains not in r.label:
                continue
        filtered.append(r)
    return filtered


def top_n(results: List[BatchResult], n: int) -> List[BatchResult]:
    """Return the n fastest results by mean time."""
    if not results:
        return []
    valid = [r for r in results if r.times]
    ranked = sorted(valid, key=lambda r: sum(r.times) / len(r.times))
    return ranked[:n]
