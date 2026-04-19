"""Merge multiple BatchResult collections into unified results."""

from dataclasses import dataclass, field
from typing import List, Dict
from batchmark.runner import BatchResult, RunResult
from batchmark.stats import summarize


@dataclass
class MergedBatch:
    label: str
    runs: List[RunResult]
    sources: List[str]

    @property
    def times(self) -> List[float]:
        return [r.elapsed for r in self.runs if r.success]

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.success)

    @property
    def total(self) -> int:
        return len(self.runs)


@dataclass
class MergeResult:
    batches: List[MergedBatch] = field(default_factory=list)

    def labels(self) -> List[str]:
        return [b.label for b in self.batches]

    def get(self, label: str) -> MergedBatch | None:
        for b in self.batches:
            if b.label == label:
                return b
        return None


def merge(sources: List[tuple[str, List[BatchResult]]]) -> MergeResult:
    """Merge named sources of BatchResult lists into a single MergeResult.

    Args:
        sources: list of (source_name, list_of_BatchResult) tuples
    """
    if not sources:
        raise ValueError("No sources provided to merge")

    accumulated: Dict[str, Dict] = {}

    for source_name, batches in sources:
        for batch in batches:
            label = batch.label
            if label not in accumulated:
                accumulated[label] = {"runs": [], "sources": []}
            accumulated[label]["runs"].extend(batch.runs)
            if source_name not in accumulated[label]["sources"]:
                accumulated[label]["sources"].append(source_name)

    merged = [
        MergedBatch(label=label, runs=data["runs"], sources=data["sources"])
        for label, data in accumulated.items()
    ]
    return MergeResult(batches=merged)


def format_merge_summary(result: MergeResult) -> str:
    lines = ["Merge Summary", "=" * 40]
    for mb in result.batches:
        stats = summarize(mb.times) if mb.times else None
        mean_str = f"{stats['mean']:.4f}s" if stats else "N/A"
        lines.append(
            f"{mb.label}: {mb.success_count}/{mb.total} ok, mean={mean_str}, "
            f"sources={','.join(mb.sources)}"
        )
    return "\n".join(lines)
