"""capper.py — cap (clamp) run times to a configurable maximum elapsed value.

Useful for preventing runaway outliers from skewing statistics while
preserving the shape of the rest of the distribution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from batchmark.runner import BatchResult, RunResult


@dataclass
class CappedBatch:
    label: str
    runs: List[RunResult]
    cap: float
    capped_count: int

    @property
    def total(self) -> int:
        return len(self.runs)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class CapResult:
    batches: List[CappedBatch] = field(default_factory=list)

    @property
    def total_capped(self) -> int:
        return sum(b.capped_count for b in self.batches)


def _cap_run(run: RunResult, cap: float) -> RunResult:
    """Return a new RunResult with elapsed clamped to *cap*."""
    if run.elapsed <= cap:
        return run
    return RunResult(elapsed=cap, returncode=run.returncode)


def cap_batch(batch: BatchResult, cap: float) -> CappedBatch:
    """Clamp every run in *batch* whose elapsed exceeds *cap*."""
    if cap <= 0:
        raise ValueError(f"cap must be positive, got {cap}")
    capped_runs: List[RunResult] = []
    capped_count = 0
    for run in batch.runs:
        new_run = _cap_run(run, cap)
        if new_run.elapsed < run.elapsed:
            capped_count += 1
        capped_runs.append(new_run)
    return CappedBatch(label=batch.label, runs=capped_runs, cap=cap, capped_count=capped_count)


def cap_all(batches: List[BatchResult], cap: float) -> CapResult:
    """Apply :func:`cap_batch` to every batch in *batches*."""
    return CapResult(batches=[cap_batch(b, cap) for b in batches])


def format_cap_summary(result: CapResult) -> str:
    """Return a human-readable summary of capping results."""
    lines = ["Cap Summary", "-" * 40]
    for b in result.batches:
        pct = (b.capped_count / b.total * 100) if b.total else 0.0
        lines.append(
            f"  {b.label}: {b.capped_count}/{b.total} runs capped "
            f"({pct:.1f}%) at cap={b.cap:.4f}s"
        )
    lines.append(f"  Total capped: {result.total_capped}")
    return "\n".join(lines)
