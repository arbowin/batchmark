"""Clamp elapsed times in BatchResults to a [min_ms, max_ms] range."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import BatchResult, RunResult


@dataclass
class ClampedBatch:
    label: str
    runs: List[RunResult]
    clamped_count: int

    @property
    def total(self) -> int:
        return len(self.runs)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class ClampResult:
    batches: List[ClampedBatch] = field(default_factory=list)

    @property
    def total_clamped(self) -> int:
        return sum(b.clamped_count for b in self.batches)


def _clamp_run(
    run: RunResult,
    min_ms: Optional[float],
    max_ms: Optional[float],
) -> tuple[RunResult, bool]:
    """Return a (possibly new) RunResult with elapsed clamped, plus a flag."""
    elapsed = run.elapsed
    clamped = False
    if min_ms is not None and elapsed < min_ms:
        elapsed = min_ms
        clamped = True
    if max_ms is not None and elapsed > max_ms:
        elapsed = max_ms
        clamped = True
    if not clamped:
        return run, False
    return RunResult(
        command=run.command,
        elapsed=elapsed,
        returncode=run.returncode,
        stdout=run.stdout,
        stderr=run.stderr,
    ), True


def clamp_batch(
    batch: BatchResult,
    min_ms: Optional[float] = None,
    max_ms: Optional[float] = None,
) -> ClampedBatch:
    """Clamp all runs in *batch* to [min_ms, max_ms]."""
    if min_ms is not None and max_ms is not None and min_ms > max_ms:
        raise ValueError(f"min_ms ({min_ms}) must be <= max_ms ({max_ms})")
    new_runs: List[RunResult] = []
    clamped_count = 0
    for run in batch.runs:
        new_run, was_clamped = _clamp_run(run, min_ms, max_ms)
        new_runs.append(new_run)
        if was_clamped:
            clamped_count += 1
    return ClampedBatch(label=batch.label, runs=new_runs, clamped_count=clamped_count)


def clamp_all(
    batches: List[BatchResult],
    min_ms: Optional[float] = None,
    max_ms: Optional[float] = None,
) -> ClampResult:
    """Clamp every batch in *batches*."""
    return ClampResult(batches=[clamp_batch(b, min_ms, max_ms) for b in batches])


def format_clamp_summary(result: ClampResult) -> str:
    lines = ["Clamp summary:", f"  total clamped runs : {result.total_clamped}"]
    for b in result.batches:
        lines.append(
            f"  {b.label}: {b.clamped_count}/{b.total} runs clamped"
        )
    return "\n".join(lines)
