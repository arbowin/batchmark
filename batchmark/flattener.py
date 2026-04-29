"""Flatten nested or grouped BatchResults into a single list."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from batchmark.runner import BatchResult, RunResult


@dataclass
class FlattenedBatch:
    label: str
    runs: List[RunResult]
    source_group: Optional[str] = None

    def total(self) -> int:
        return len(self.runs)

    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class FlattenResult:
    batches: List[FlattenedBatch] = field(default_factory=list)

    def count(self) -> int:
        return len(self.batches)

    def total_runs(self) -> int:
        return sum(b.total() for b in self.batches)

    def labels(self) -> List[str]:
        return [b.label for b in self.batches]


def _flatten_batch(batch: BatchResult, group: Optional[str] = None) -> FlattenedBatch:
    return FlattenedBatch(
        label=batch.label,
        runs=list(batch.runs),
        source_group=group,
    )


def flatten(
    sources: Dict[str, List[BatchResult]],
    merge_same_label: bool = False,
) -> FlattenResult:
    """Flatten a dict of group_name -> [BatchResult] into a FlattenResult.

    If *merge_same_label* is True, runs from batches sharing the same label
    (across groups) are merged into a single FlattenedBatch.
    """
    if not sources:
        raise ValueError("sources must not be empty")

    merged: Dict[str, FlattenedBatch] = {}
    ordered: List[FlattenedBatch] = []

    for group_name, batches in sources.items():
        for batch in batches:
            fb = _flatten_batch(batch, group=group_name)
            if merge_same_label:
                if batch.label in merged:
                    merged[batch.label].runs.extend(fb.runs)
                else:
                    merged[batch.label] = fb
                    ordered.append(merged[batch.label])
            else:
                ordered.append(fb)

    return FlattenResult(batches=ordered)


def format_flattened(result: FlattenResult) -> str:
    lines = [f"Flattened batches: {result.count()}  total runs: {result.total_runs()}"]
    for fb in result.batches:
        group_tag = f" [{fb.source_group}]" if fb.source_group else ""
        lines.append(
            f"  {fb.label}{group_tag}: {fb.total()} runs, "
            f"{fb.success_count()} ok"
        )
    return "\n".join(lines)
