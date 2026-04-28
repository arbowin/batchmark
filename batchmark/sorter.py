"""Sort BatchResult collections by various criteria."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

from batchmark.runner import BatchResult
from batchmark.stats import mean, median

SortKey = Literal["mean", "median", "label", "success_rate", "total"]
SortOrder = Literal["asc", "desc"]


@dataclass
class SortResult:
    batches: List[BatchResult]
    key: SortKey
    order: SortOrder

    def __len__(self) -> int:
        return len(self.batches)


def _success_rate(batch: BatchResult) -> float:
    total = len(batch.runs)
    if total == 0:
        return 0.0
    return batch.success_count / total


def _sort_key(batch: BatchResult, key: SortKey) -> float | str:
    if key == "mean":
        times = [r.elapsed for r in batch.runs]
        return mean(times) if times else float("inf")
    if key == "median":
        times = [r.elapsed for r in batch.runs]
        return median(times) if times else float("inf")
    if key == "label":
        return batch.label
    if key == "success_rate":
        return _success_rate(batch)
    if key == "total":
        return len(batch.runs)
    raise ValueError(f"Unknown sort key: {key!r}")


def sort_batches(
    batches: List[BatchResult],
    key: SortKey = "mean",
    order: SortOrder = "asc",
) -> SortResult:
    if not batches:
        raise ValueError("Cannot sort an empty list of batches.")
    reverse = order == "desc"
    sorted_batches = sorted(batches, key=lambda b: _sort_key(b, key), reverse=reverse)
    return SortResult(batches=sorted_batches, key=key, order=order)


def format_sort_result(result: SortResult) -> str:
    lines = [f"Sorted by {result.key!r} ({result.order}):", ""]
    for i, batch in enumerate(result.batches, 1):
        times = [r.elapsed for r in batch.runs]
        avg = mean(times) if times else 0.0
        rate = _success_rate(batch)
        lines.append(
            f"  {i:>3}. {batch.label:<30}  mean={avg:.4f}s  "
            f"success={rate:.0%}  n={len(batch.runs)}"
        )
    return "\n".join(lines)
