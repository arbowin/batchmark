"""trimmer.py — trim outlier runs from batch results by percentile bounds."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from batchmark.runner import BatchResult, RunResult


@dataclass
class TrimmedBatch:
    label: str
    runs: List[RunResult]
    removed_count: int
    lower_bound: float
    upper_bound: float

    @property
    def total(self) -> int:
        return len(self.runs)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class TrimResult:
    batches: List[TrimmedBatch] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return sum(b.removed_count for b in self.batches)


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = pct / 100.0 * (len(sorted_vals) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def trim_batch(batch: BatchResult, lower_pct: float = 5.0, upper_pct: float = 95.0) -> TrimmedBatch:
    """Remove runs whose elapsed time falls outside [lower_pct, upper_pct] percentiles."""
    if lower_pct < 0 or upper_pct > 100 or lower_pct >= upper_pct:
        raise ValueError(f"Invalid percentile range: [{lower_pct}, {upper_pct}]")
    times = [r.elapsed for r in batch.runs]
    lo = _percentile(times, lower_pct)
    hi = _percentile(times, upper_pct)
    kept = [r for r in batch.runs if lo <= r.elapsed <= hi]
    removed = len(batch.runs) - len(kept)
    return TrimmedBatch(
        label=batch.label,
        runs=kept,
        removed_count=removed,
        lower_bound=lo,
        upper_bound=hi,
    )


def trim_all(batches: List[BatchResult], lower_pct: float = 5.0, upper_pct: float = 95.0) -> TrimResult:
    """Trim all batches and return a TrimResult."""
    return TrimResult(batches=[trim_batch(b, lower_pct, upper_pct) for b in batches])


def format_trim_summary(result: TrimResult) -> str:
    lines = ["Trim Summary", "=" * 40]
    for b in result.batches:
        lines.append(
            f"{b.label}: kept {b.total}, removed {b.removed_count} "
            f"(bounds: [{b.lower_bound:.4f}s, {b.upper_bound:.4f}s])"
        )
    lines.append(f"Total removed: {result.total_removed}")
    return "\n".join(lines)
