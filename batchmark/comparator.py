"""Compare multiple BatchResults and produce a comparison summary."""

from dataclasses import dataclass
from typing import List, Dict
from batchmark.runner import BatchResult
from batchmark.stats import summarize


@dataclass
class ComparisonRow:
    label: str
    mean: float
    median: float
    stdev: float
    success_rate: float
    rank: int


@dataclass
class ComparisonResult:
    rows: List[ComparisonRow]
    baseline_label: str

    def winner(self) -> ComparisonRow:
        return next(r for r in self.rows if r.rank == 1)


def compare(results: List[BatchResult], baseline_label: str = None) -> ComparisonResult:
    """Compare a list of BatchResults by mean execution time."""
    if not results:
        raise ValueError("No results to compare")

    rows: List[ComparisonRow] = []
    for br in results:
        stats = summarize(br)
        total = len(br.times)
        success_rate = (br.success_count / total * 100) if total > 0 else 0.0
        rows.append(ComparisonRow(
            label=br.label,
            mean=stats["mean"],
            median=stats["median"],
            stdev=stats["stdev"],
            success_rate=success_rate,
            rank=0,
        ))

    rows.sort(key=lambda r: r.mean)
    for i, row in enumerate(rows):
        row.rank = i + 1

    if baseline_label is None:
        baseline_label = rows[0].label

    return ComparisonResult(rows=rows, baseline_label=baseline_label)


def format_comparison(result: ComparisonResult) -> str:
    """Render a comparison table as a string."""
    header = f"{'Rank':<6}{'Label':<30}{'Mean(s)':<12}{'Median(s)':<12}{'Stdev':<10}{'Success%':<10}"
    sep = "-" * len(header)
    lines = ["Comparison Results", sep, header, sep]
    for row in result.rows:
        marker = " *" if row.label == result.baseline_label else ""
        lines.append(
            f"{row.rank:<6}{row.label:<30}{row.mean:<12.4f}{row.median:<12.4f}"
            f"{row.stdev:<10.4f}{row.success_rate:<10.1f}{marker}"
        )
    lines.append(sep)
    lines.append(f"Baseline: {result.baseline_label}  |  Winner: {result.winner().label}")
    return "\n".join(lines)
