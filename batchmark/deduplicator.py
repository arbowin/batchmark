"""Deduplication of BatchResult entries based on label and timing similarity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import BatchResult
from batchmark.stats import mean


@dataclass
class DeduplicationResult:
    kept: List[BatchResult]
    removed: List[BatchResult]
    total_before: int
    total_after: int

    @property
    def removed_count(self) -> int:
        return len(self.removed)


def _batch_mean(batch: BatchResult) -> float:
    """Return mean elapsed time for a batch, or 0.0 if no runs."""
    times = [r.elapsed for r in batch.runs]
    return mean(times) if times else 0.0


def _is_duplicate(
    a: BatchResult,
    b: BatchResult,
    time_tolerance: float = 0.01,
) -> bool:
    """Return True if two BatchResults share a label and near-identical mean time."""
    if a.label != b.label:
        return False
    mean_a = _batch_mean(a)
    mean_b = _batch_mean(b)
    if mean_a == 0.0 and mean_b == 0.0:
        return True
    denom = max(mean_a, mean_b)
    return abs(mean_a - mean_b) / denom <= time_tolerance


def deduplicate(
    batches: List[BatchResult],
    time_tolerance: float = 0.01,
) -> DeduplicationResult:
    """Remove duplicate BatchResults, keeping the first occurrence of each.

    Two batches are considered duplicates if they share the same label and
    their mean elapsed times are within *time_tolerance* (relative).
    """
    if not batches:
        return DeduplicationResult(
            kept=[], removed=[], total_before=0, total_after=0
        )

    kept: List[BatchResult] = []
    removed: List[BatchResult] = []

    for candidate in batches:
        is_dup = any(
            _is_duplicate(candidate, k, time_tolerance) for k in kept
        )
        if is_dup:
            removed.append(candidate)
        else:
            kept.append(candidate)

    return DeduplicationResult(
        kept=kept,
        removed=removed,
        total_before=len(batches),
        total_after=len(kept),
    )


def format_deduplication(result: DeduplicationResult) -> str:
    """Return a human-readable summary of the deduplication result."""
    lines = [
        f"Deduplication summary",
        f"  Before : {result.total_before} batch(es)",
        f"  After  : {result.total_after} batch(es)",
        f"  Removed: {result.removed_count} duplicate(s)",
    ]
    if result.removed:
        labels = ", ".join(b.label for b in result.removed)
        lines.append(f"  Labels removed: {labels}")
    return "\n".join(lines)
