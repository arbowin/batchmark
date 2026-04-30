"""cutter.py — slice a fixed window of runs from each batch by index range."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from batchmark.runner import BatchResult, RunResult


@dataclass
class CutBatch:
    label: str
    runs: List[RunResult]

    @property
    def total(self) -> int:
        return len(self.runs)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class CutResult:
    batches: List[CutBatch]
    start: int
    stop: int

    @property
    def count(self) -> int:
        return len(self.batches)


def _validate_range(start: int, stop: int, total: int) -> None:
    if start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    if stop < start:
        raise ValueError(f"stop must be >= start, got stop={stop} start={start}")
    if start > total:
        raise ValueError(
            f"start ({start}) exceeds batch size ({total})"
        )


def cut_batch(batch: BatchResult, start: int, stop: int) -> CutBatch:
    """Return a CutBatch containing runs[start:stop] from *batch*."""
    runs = list(batch.runs)
    _validate_range(start, stop, len(runs))
    sliced = runs[start:stop]
    return CutBatch(label=batch.label, runs=sliced)


def cut_all(batches: List[BatchResult], start: int, stop: int) -> CutResult:
    """Apply cut_batch to every batch and return a CutResult."""
    if not batches:
        raise ValueError("batches must not be empty")
    cut_batches = [cut_batch(b, start, stop) for b in batches]
    return CutResult(batches=cut_batches, start=start, stop=stop)


def format_cut_summary(result: CutResult) -> str:
    """Return a human-readable summary of a CutResult."""
    lines = [f"Cut [{result.start}:{result.stop}]  ({result.count} batch(es))"]
    for cb in result.batches:
        lines.append(
            f"  {cb.label}: {cb.total} run(s), {cb.success_count} ok"
        )
    return "\n".join(lines)
