"""Interpolate missing time-series data points in BatchResult runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from batchmark.runner import BatchResult, RunResult


@dataclass
class InterpolatedBatch:
    label: str
    runs: List[RunResult]
    added_count: int

    @property
    def total(self) -> int:
        return len(self.runs)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class InterpolateResult:
    batches: List[InterpolatedBatch] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.batches)

    @property
    def total_added(self) -> int:
        return sum(b.added_count for b in self.batches)


def _linear_fill(times: List[float], target: int) -> List[float]:
    """Insert linearly interpolated values until len == target."""
    if not times or target <= len(times):
        return list(times)
    result = list(times)
    while len(result) < target:
        new_vals: List[float] = []
        for i in range(len(result) - 1):
            new_vals.append(result[i])
            new_vals.append((result[i] + result[i + 1]) / 2.0)
        new_vals.append(result[-1])
        result = new_vals
    return result[:target]


def interpolate_batch(batch: BatchResult, target: int) -> InterpolatedBatch:
    """Expand *batch* to *target* runs using linear interpolation."""
    if target < 1:
        raise ValueError("target must be >= 1")
    original_runs = list(batch.runs)
    if len(original_runs) >= target:
        return InterpolatedBatch(label=batch.label, runs=original_runs, added_count=0)

    elapsed_vals = [r.elapsed for r in original_runs]
    filled = _linear_fill(elapsed_vals, target)
    added = target - len(original_runs)

    new_runs: List[RunResult] = list(original_runs)
    for elapsed in filled[len(original_runs):]:
        new_runs.append(RunResult(command=batch.runs[0].command if batch.runs else "",
                                  elapsed=elapsed, returncode=0, stdout="", stderr=""))
    return InterpolatedBatch(label=batch.label, runs=new_runs, added_count=added)


def interpolate(batches: Sequence[BatchResult], target: int) -> InterpolateResult:
    """Interpolate all *batches* to *target* run count."""
    if not batches:
        raise ValueError("batches must not be empty")
    result = InterpolateResult()
    for batch in batches:
        result.batches.append(interpolate_batch(batch, target))
    return result


def format_interpolate_summary(result: InterpolateResult) -> str:
    lines = [f"Interpolation summary ({result.count} batch(es), {result.total_added} point(s) added)"]
    for b in result.batches:
        lines.append(f"  {b.label}: {b.total} runs (+{b.added_count} interpolated)")
    return "\n".join(lines)
