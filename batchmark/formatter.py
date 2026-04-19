"""Output formatting for batchmark results."""

from batchmark.runner import BatchResult
from batchmark.stats import summarize


def format_summary(label: str, result: BatchResult) -> str:
    """Format a BatchResult into a human-readable summary string."""
    stats = summarize(result.times)
    lines = [
        f"Command : {label}",
        f"Runs    : {result.iterations} total, {result.success_count} succeeded, "
        f"{result.iterations - result.success_count} failed",
        f"Mean    : {stats['mean']:.4f}s",
        f"Median  : {stats['median']:.4f}s",
        f"Std Dev : {stats['stdev']:.4f}s",
        f"Min     : {stats['min']:.4f}s",
        f"Max     : {stats['max']:.4f}s",
    ]
    return "\n".join(lines)


def format_table(results: dict[str, BatchResult]) -> str:
    """Format multiple BatchResults as an aligned table."""
    if not results:
        return "No results to display."

    header = f"{'Command':<40} {'Runs':>5} {'OK':>5} {'Mean':>10} {'Median':>10} {'Stdev':>10} {'Min':>10} {'Max':>10}"
    separator = "-" * len(header)
    rows = [header, separator]

    for label, result in results.items():
        stats = summarize(result.times)
        short_label = label[:38] + ".." if len(label) > 40 else label
        row = (
            f"{short_label:<40}"
            f" {result.iterations:>5}"
            f" {result.success_count:>5}"
            f" {stats['mean']:>10.4f}"
            f" {stats['median']:>10.4f}"
            f" {stats['stdev']:>10.4f}"
            f" {stats['min']:>10.4f}"
            f" {stats['max']:>10.4f}"
        )
        rows.append(row)

    return "\n".join(rows)
