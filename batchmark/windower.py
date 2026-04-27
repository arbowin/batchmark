"""Sliding window analysis over BatchResult sequences."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import BatchResult
from batchmark.stats import mean, stdev


@dataclass
class WindowStats:
    start: int
    end: int
    label: str
    mean: float
    stdev: float
    run_count: int
    success_count: int

    @property
    def success_rate(self) -> float:
        return self.success_count / self.run_count if self.run_count else 0.0


@dataclass
class WindowResult:
    label: str
    window_size: int
    windows: List[WindowStats] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.windows)

    def means(self) -> List[float]:
        return [w.mean for w in self.windows]


def _times(batch: BatchResult) -> List[float]:
    return [r.elapsed for r in batch.runs]


def _success_count(batch: BatchResult) -> int:
    return sum(1 for r in batch.runs if r.returncode == 0)


def slide(batches: List[BatchResult], window_size: int) -> List[WindowResult]:
    """Apply a sliding window of *window_size* batches over the list.

    Batches with the same label are grouped together before windowing.
    """
    if window_size < 1:
        raise ValueError("window_size must be >= 1")
    if not batches:
        raise ValueError("batches must not be empty")

    by_label: dict[str, List[BatchResult]] = {}
    for b in batches:
        by_label.setdefault(b.label, []).append(b)

    results: List[WindowResult] = []
    for label, group in by_label.items():
        wr = WindowResult(label=label, window_size=window_size)
        for i in range(len(group) - window_size + 1):
            window = group[i : i + window_size]
            all_times = [t for b in window for t in _times(b)]
            sc = sum(_success_count(b) for b in window)
            rc = sum(len(b.runs) for b in window)
            ws = WindowStats(
                start=i,
                end=i + window_size - 1,
                label=label,
                mean=mean(all_times) if all_times else 0.0,
                stdev=stdev(all_times) if len(all_times) > 1 else 0.0,
                run_count=rc,
                success_count=sc,
            )
            wr.windows.append(ws)
        results.append(wr)
    return results


def format_window_result(wr: WindowResult) -> str:
    lines = [f"Window analysis — label: {wr.label!r}  size: {wr.window_size}"]
    lines.append(f"  {'#':>4}  {'start':>5}  {'end':>5}  {'mean':>10}  {'stdev':>10}  {'ok%':>6}")
    for idx, w in enumerate(wr.windows):
        lines.append(
            f"  {idx:>4}  {w.start:>5}  {w.end:>5}  "
            f"{w.mean:>10.4f}  {w.stdev:>10.4f}  {w.success_rate * 100:>5.1f}%"
        )
    return "\n".join(lines)
