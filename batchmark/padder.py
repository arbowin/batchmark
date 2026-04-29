"""Pad batch run sets to a target count by repeating or filling with synthetic runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from batchmark.runner import BatchResult, RunResult


@dataclass
class PaddedBatch:
    label: str
    runs: List[RunResult]
    original_count: int
    added_count: int

    @property
    def total(self) -> int:
        return len(self.runs)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class PadResult:
    batches: List[PaddedBatch] = field(default_factory=list)

    @property
    def total_added(self) -> int:
        return sum(b.added_count for b in self.batches)


def _mean_elapsed(runs: List[RunResult]) -> float:
    if not runs:
        return 0.0
    return sum(r.elapsed for r in runs) / len(runs)


def _synthetic_run(runs: List[RunResult]) -> RunResult:
    """Create a synthetic run using the mean elapsed time of existing runs."""
    avg = _mean_elapsed(runs)
    return RunResult(elapsed=avg, returncode=0, stdout="", stderr="")


def pad_batch(batch: BatchResult, target: int, strategy: str = "repeat") -> PaddedBatch:
    """Pad a batch to *target* runs.

    Strategies:
      - ``repeat``: cycle through existing runs in order.
      - ``mean``:   fill with a synthetic run whose elapsed is the mean.
    """
    if target < 1:
        raise ValueError("target must be >= 1")
    runs = list(batch.runs)
    original = len(runs)
    if original >= target:
        return PaddedBatch(label=batch.label, runs=runs[:target],
                           original_count=original, added_count=0)
    needed = target - original
    if strategy == "mean":
        filler = [_synthetic_run(runs) for _ in range(needed)]
    elif strategy == "repeat":
        filler = [runs[i % original] for i in range(needed)]
    else:
        raise ValueError(f"Unknown padding strategy: {strategy!r}")
    return PaddedBatch(label=batch.label, runs=runs + filler,
                       original_count=original, added_count=needed)


def pad_all(batches: List[BatchResult], target: int, strategy: str = "repeat") -> PadResult:
    """Pad every batch in *batches* to *target* runs."""
    return PadResult(batches=[pad_batch(b, target, strategy) for b in batches])


def format_pad_summary(result: PadResult) -> str:
    lines = ["Padding summary:", f"  Total runs added : {result.total_added}"]
    for b in result.batches:
        lines.append(
            f"  {b.label:<30} original={b.original_count}  added={b.added_count}  total={b.total}"
        )
    return "\n".join(lines)
