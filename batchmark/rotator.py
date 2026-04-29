"""rotator.py – rotate (circularly shift) runs within each BatchResult.

Useful for testing scheduler fairness or simulating time-shifted workloads.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import BatchResult, RunResult


@dataclass
class RotatedBatch:
    label: str
    runs: List[RunResult]
    shift: int

    @property
    def total(self) -> int:
        return len(self.runs)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class RotateResult:
    batches: List[RotatedBatch]

    @property
    def count(self) -> int:
        return len(self.batches)


def _rotate(runs: List[RunResult], shift: int) -> List[RunResult]:
    """Return *runs* circularly shifted left by *shift* positions."""
    if not runs:
        return []
    n = len(runs)
    shift = shift % n
    return runs[shift:] + runs[:shift]


def rotate_batch(batch: BatchResult, shift: int) -> RotatedBatch:
    """Rotate a single BatchResult by *shift* positions."""
    if shift < 0:
        raise ValueError(f"shift must be non-negative, got {shift}")
    rotated = _rotate(list(batch.runs), shift)
    return RotatedBatch(label=batch.label, runs=rotated, shift=shift)


def rotate_all(
    batches: List[BatchResult],
    shift: int = 1,
    per_batch: Optional[List[int]] = None,
) -> RotateResult:
    """Rotate every batch in *batches*.

    If *per_batch* is supplied it must have the same length as *batches* and
    each entry overrides the global *shift* for that batch.
    """
    if not batches:
        raise ValueError("batches must not be empty")
    if per_batch is not None and len(per_batch) != len(batches):
        raise ValueError(
            f"per_batch length ({len(per_batch)}) must match batches length ({len(batches)})"
        )
    result: List[RotatedBatch] = []
    for i, batch in enumerate(batches):
        s = per_batch[i] if per_batch is not None else shift
        result.append(rotate_batch(batch, s))
    return RotateResult(batches=result)


def format_rotate_summary(result: RotateResult) -> str:
    """Return a human-readable summary of rotated batches."""
    lines = ["Rotate Summary", "=" * 30]
    for rb in result.batches:
        lines.append(
            f"  {rb.label}: {rb.total} runs, shift={rb.shift}, "
            f"success={rb.success_count}/{rb.total}"
        )
    return "\n".join(lines)
