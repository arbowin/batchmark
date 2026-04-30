"""Truncate batch runs to a fixed maximum count per batch."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from batchmark.runner import BatchResult, RunResult


@dataclass
class TruncatedBatch:
    label: str
    runs: List[RunResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.runs)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class TruncateResult:
    batches: List[TruncatedBatch] = field(default_factory=list)
    max_runs: int = 0

    @property
    def count(self) -> int:
        return len(self.batches)

    @property
    def total_removed(self) -> int:
        return sum(b._original_total - b.total for b in self.batches
                   if hasattr(b, '_original_total'))


def _truncate_batch(batch: BatchResult, max_runs: int) -> TruncatedBatch:
    """Truncate a single batch to at most max_runs runs."""
    if max_runs <= 0:
        raise ValueError(f"max_runs must be positive, got {max_runs}")
    runs = list(batch.runs[:max_runs])
    tb = TruncatedBatch(label=batch.label, runs=runs)
    tb._original_total = len(batch.runs)  # type: ignore[attr-defined]
    return tb


def truncate(batches: List[BatchResult], max_runs: int) -> TruncateResult:
    """Truncate all batches to at most max_runs runs each."""
    if not batches:
        raise ValueError("batches list must not be empty")
    if max_runs <= 0:
        raise ValueError(f"max_runs must be positive, got {max_runs}")
    result = TruncateResult(max_runs=max_runs)
    for batch in batches:
        result.batches.append(_truncate_batch(batch, max_runs))
    return result


def format_truncate_summary(result: TruncateResult) -> str:
    """Return a human-readable summary of truncation results."""
    lines = [f"Truncation summary (max_runs={result.max_runs})"]
    for tb in result.batches:
        original = getattr(tb, '_original_total', tb.total)
        removed = original - tb.total
        lines.append(
            f"  {tb.label}: {original} -> {tb.total} runs"
            + (f" ({removed} removed)" if removed else "")
        )
    return "\n".join(lines)
