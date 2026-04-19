"""High-level pipeline: run, filter, compare, and export results."""

from typing import List, Optional
from batchmark.runner import BatchResult, benchmark_command
from batchmark.filter import FilterCriteria, filter_results, top_n
from batchmark.comparator import compare, format_comparison
from batchmark.exporter import export
from batchmark.formatter import format_table


def run_pipeline(
    commands: List[str],
    iterations: int = 10,
    criteria: Optional[FilterCriteria] = None,
    top: Optional[int] = None,
    export_path: Optional[str] = None,
    export_fmt: str = "json",
) -> str:
    """
    Run benchmarks for all commands, apply filters, and return
    a formatted comparison string. Optionally export results.

    Args:
        commands: Shell commands to benchmark.
        iterations: Number of runs per command.
        criteria: Optional filter criteria to apply.
        top: If set, keep only the top N fastest results.
        export_path: If set, export results to this file path.
        export_fmt: Export format, 'json' or 'csv'.

    Returns:
        Formatted comparison table as a string.
    """
    if not commands:
        raise ValueError("At least one command is required.")

    results: List[BatchResult] = [
        benchmark_command(cmd, iterations) for cmd in commands
    ]

    if criteria is not None:
        results = filter_results(results, criteria)

    if top is not None:
        results = top_n(results, top)

    if not results:
        return "No results matched the given criteria."

    if export_path:
        export(results, export_path, fmt=export_fmt)

    comparison = compare(results)
    return format_comparison(comparison)
