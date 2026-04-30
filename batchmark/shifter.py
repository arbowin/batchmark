"""shifter.py — shift batch run times by a fixed offset or scale factor."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from batchmark.runner import BatchResult, RunResult


@dataclass
class ShiftedBatch:
    label: str
    runs: List[RunResult]

    @property
    def total(self) -> int:
        return len(self.runs)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class ShiftResult:
    batches: List[ShiftedBatch] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.batches)


def _shift_run(run: RunResult, offset: float, scale: float) -> RunResult:
    """Return a new RunResult with elapsed time shifted and scaled."""
    new_elapsed = max(0.0, run.elapsed * scale + offset)
    return RunResult(
        command=run.command,
        elapsed=new_elapsed,
        returncode=run.returncode,
        stdout=run.stdout,
        stderr=run.stderr,
    )


def shift_batch(
    batch: BatchResult,
    offset: float = 0.0,
    scale: float = 1.0,
) -> ShiftedBatch:
    """Shift all run times in a batch by *offset* seconds and multiply by *scale*."""
    if scale < 0:
        raise ValueError(f"scale must be non-negative, got {scale}")
    shifted = [_shift_run(r, offset, scale) for r in batch.runs]
    return ShiftedBatch(label=batch.label, runs=shifted)


def shift_all(
    batches: List[BatchResult],
    offset: float = 0.0,
    scale: float = 1.0,
) -> ShiftResult:
    """Apply shift_batch to every BatchResult in *batches*."""
    if not batches:
        raise ValueError("batches must not be empty")
    return ShiftResult(batches=[shift_batch(b, offset=offset, scale=scale) for b in batches])


def format_shift_summary(result: ShiftResult, precision: int = 4) -> str:
    """Return a human-readable summary of shifted batches."""
    lines = ["Shift Summary", "=" * 40]
    for sb in result.batches:
        times = [r.elapsed for r in sb.runs]
        mean = sum(times) / len(times) if times else 0.0
        lines.append(
            f"  {sb.label}: {sb.total} runs, "
            f"mean={mean:.{precision}f}s, "
            f"ok={sb.success_count}/{sb.total}"
        )
    return "\n".join(lines)
