"""Pivot BatchResult data by a chosen dimension (label vs. metric)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from batchmark.runner import BatchResult
from batchmark.stats import mean, median, stdev

_METRICS = ("mean", "median", "stdev", "min", "max", "success_rate")


@dataclass
class PivotCell:
    label: str
    metric: str
    value: float


@dataclass
class PivotResult:
    metrics: List[str]
    labels: List[str]
    cells: List[PivotCell] = field(default_factory=list)

    def get(self, label: str, metric: str) -> Optional[float]:
        for c in self.cells:
            if c.label == label and c.metric == metric:
                return c.value
        return None


def _compute_metric(batch: BatchResult, metric: str) -> float:
    times = [r.elapsed for r in batch.runs]
    if not times:
        return 0.0
    if metric == "mean":
        return mean(times)
    if metric == "median":
        return median(times)
    if metric == "stdev":
        return stdev(times)
    if metric == "min":
        return min(times)
    if metric == "max":
        return max(times)
    if metric == "success_rate":
        total = len(batch.runs)
        ok = sum(1 for r in batch.runs if r.returncode == 0)
        return ok / total if total else 0.0
    raise ValueError(f"Unknown metric: {metric}")


def pivot(
    batches: List[BatchResult],
    metrics: Optional[List[str]] = None,
) -> PivotResult:
    """Build a pivot table: rows=labels, columns=metrics."""
    if not batches:
        raise ValueError("pivot requires at least one BatchResult")
    chosen = list(metrics) if metrics else list(_METRICS)
    for m in chosen:
        if m not in _METRICS:
            raise ValueError(f"Unknown metric '{m}'. Choose from {_METRICS}")
    labels = [b.label for b in batches]
    cells: List[PivotCell] = []
    for batch in batches:
        for metric in chosen:
            cells.append(PivotCell(batch.label, metric, _compute_metric(batch, metric)))
    return PivotResult(metrics=chosen, labels=labels, cells=cells)


def format_pivot(result: PivotResult, precision: int = 4) -> str:
    """Render the pivot table as a plain-text grid."""
    col_w = max(len(m) for m in result.metrics) + 2
    label_w = max((len(l) for l in result.labels), default=5) + 2
    header = f"{'label':<{label_w}}" + "".join(f"{m:>{col_w}}" for m in result.metrics)
    sep = "-" * len(header)
    rows = [header, sep]
    for label in result.labels:
        row = f"{label:<{label_w}}"
        for metric in result.metrics:
            val = result.get(label, metric)
            row += f"{round(val, precision):>{col_w}}"
        rows.append(row)
    return "\n".join(rows)
