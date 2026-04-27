"""Rolling average smoother for batch timing series."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from batchmark.runner import BatchResult


@dataclass
class SmoothedPoint:
    index: int
    raw_mean: float
    smoothed_mean: float


@dataclass
class SmoothedBatch:
    label: str
    points: List[SmoothedPoint] = field(default_factory=list)

    @property
    def smoothed_means(self) -> List[float]:
        return [p.smoothed_mean for p in self.points]

    @property
    def raw_means(self) -> List[float]:
        return [p.raw_mean for p in self.points]


@dataclass
class SmoothResult:
    batches: List[SmoothedBatch] = field(default_factory=list)

    @property
    def labels(self) -> List[str]:
        return [b.label for b in self.batches]


def _chunk_means(batch: BatchResult, window: int) -> List[float]:
    """Split runs into non-overlapping windows and return per-window means."""
    runs = batch.results
    if not runs:
        return []
    means: List[float] = []
    for start in range(0, len(runs), window):
        chunk = runs[start : start + window]
        means.append(sum(r.elapsed for r in chunk) / len(chunk))
    return means


def _rolling_average(values: List[float], span: int) -> List[float]:
    """Compute a simple rolling (trailing) average with the given span."""
    if not values:
        return []
    smoothed: List[float] = []
    for i, v in enumerate(values):
        window = values[max(0, i - span + 1) : i + 1]
        smoothed.append(sum(window) / len(window))
    return smoothed


def smooth(
    batches: List[BatchResult],
    chunk_size: int = 5,
    span: int = 3,
) -> SmoothResult:
    """Smooth timing series for each batch.

    Parameters
    ----------
    batches:
        List of BatchResult objects to process.
    chunk_size:
        Number of consecutive runs to average into a single raw data point.
    span:
        Rolling-average window applied on top of the chunked means.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    if span < 1:
        raise ValueError("span must be >= 1")

    result = SmoothResult()
    for batch in batches:
        raw = _chunk_means(batch, chunk_size)
        smoothed = _rolling_average(raw, span)
        points = [
            SmoothedPoint(index=i, raw_mean=r, smoothed_mean=s)
            for i, (r, s) in enumerate(zip(raw, smoothed))
        ]
        result.batches.append(SmoothedBatch(label=batch.label, points=points))
    return result


def format_smooth(result: SmoothResult) -> str:
    """Return a human-readable summary of smoothed results."""
    lines: List[str] = []
    for sb in result.batches:
        lines.append(f"[{sb.label}]")
        if not sb.points:
            lines.append("  (no data)")
            continue
        for p in sb.points:
            lines.append(
                f"  [{p.index:>3}] raw={p.raw_mean:.4f}s  smooth={p.smoothed_mean:.4f}s"
            )
    return "\n".join(lines)
