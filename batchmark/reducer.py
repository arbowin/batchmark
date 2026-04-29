"""reducer.py – reduce multiple BatchResults into a single representative batch.

Supports two strategies:
  - 'mean'   : synthetic run per label whose elapsed equals the mean of all runs
  - 'median' : synthetic run per label whose elapsed equals the median of all runs
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal

from batchmark.runner import BatchResult, RunResult
from batchmark.stats import mean, median

Strategy = Literal["mean", "median"]


@dataclass
class ReducedBatch:
    label: str
    runs: List[RunResult]
    strategy: str
    source_count: int  # number of source batches merged

    def total(self) -> int:
        return len(self.runs)

    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class ReduceResult:
    batches: List[ReducedBatch] = field(default_factory=list)

    def count(self) -> int:
        return len(self.batches)

    def labels(self) -> List[str]:
        return [b.label for b in self.batches]


def _pick(values: List[float], strategy: Strategy) -> float:
    if not values:
        return 0.0
    if strategy == "median":
        return median(values)
    return mean(values)


def reduce(
    sources: List[List[BatchResult]],
    strategy: Strategy = "mean",
) -> ReduceResult:
    """Reduce a list of benchmark source groups into one ReduceResult.

    Each source is a list of BatchResults from one run of the pipeline.
    Batches with the same label are collapsed into a single synthetic run.
    """
    if not sources:
        raise ValueError("reduce requires at least one source")

    # Collect all elapsed times per label across all sources
    label_times: dict[str, List[float]] = {}
    label_codes: dict[str, List[int]] = {}
    source_counts: dict[str, int] = {}

    for source in sources:
        for batch in source:
            lbl = batch.label
            times = [r.elapsed for r in batch.runs]
            codes = [r.returncode for r in batch.runs]
            label_times.setdefault(lbl, []).extend(times)
            label_codes.setdefault(lbl, []).extend(codes)
            source_counts[lbl] = source_counts.get(lbl, 0) + 1

    result = ReduceResult()
    for lbl, times in label_times.items():
        chosen = _pick(times, strategy)
        # Majority vote on returncode
        codes = label_codes[lbl]
        rc = 0 if codes.count(0) >= len(codes) / 2 else 1
        synthetic_run = RunResult(elapsed=chosen, returncode=rc, stdout="", stderr="")
        result.batches.append(
            ReducedBatch(
                label=lbl,
                runs=[synthetic_run],
                strategy=strategy,
                source_count=source_counts[lbl],
            )
        )

    return result


def format_reduced(result: ReduceResult) -> str:
    lines = [f"Reduced result ({result.count()} label(s)):", ""]
    for b in result.batches:
        lines.append(
            f"  {b.label}: elapsed={b.runs[0].elapsed:.4f}s  "
            f"strategy={b.strategy}  sources={b.source_count}"
        )
    return "\n".join(lines)
