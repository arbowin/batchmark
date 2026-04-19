"""Aggregator: combine multiple BatchResults into a unified summary."""

from dataclasses import dataclass, field
from typing import List, Dict
from batchmark.runner import BatchResult, RunResult
from batchmark.stats import summarize


@dataclass
class AggregatedResult:
    label: str
    all_times: List[float]
    total_runs: int
    total_successes: int

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.total_successes / self.total_runs

    @property
    def summary(self) -> Dict[str, float]:
        return summarize(self.all_times) if self.all_times else {}


def aggregate(batches: List[BatchResult]) -> List[AggregatedResult]:
    """Merge multiple BatchResults with the same label into AggregatedResults."""
    if not batches:
        raise ValueError("No batches provided to aggregate.")

    grouped: Dict[str, AggregatedResult] = {}

    for batch in batches:
        label = batch.label
        times = [r.elapsed for r in batch.results if r.elapsed is not None]
        successes = sum(1 for r in batch.results if r.success)
        total = len(batch.results)

        if label not in grouped:
            grouped[label] = AggregatedResult(
                label=label,
                all_times=times,
                total_runs=total,
                total_successes=successes,
            )
        else:
            grouped[label].all_times.extend(times)
            grouped[label].total_runs += total
            grouped[label].total_successes += successes

    return list(grouped.values())


def format_aggregated(results: List[AggregatedResult]) -> str:
    """Return a simple text summary of aggregated results."""
    lines = ["=== Aggregated Results ==="]
    for r in results:
        s = r.summary
        lines.append(
            f"[{r.label}] runs={r.total_runs} success_rate={r.success_rate:.0%} "
            f"mean={s.get('mean', float('nan')):.4f}s "
            f"median={s.get('median', float('nan')):.4f}s "
            f"stdev={s.get('stdev', float('nan')):.4f}s"
        )
    return "\n".join(lines)
