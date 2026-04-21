"""Export benchmark results to JSON or CSV formats."""

import csv
import json
import io
from typing import List
from batchmark.runner import BatchResult
from batchmark.stats import summarize


def _build_row(br: BatchResult) -> dict:
    """Build a result row dict from a BatchResult."""
    summary = summarize(br)
    return {
        "label": br.label,
        "iterations": len(br.times),
        "success_count": br.success_count,
        "mean": summary["mean"],
        "median": summary["median"],
        "stdev": summary["stdev"],
        "min": summary["min"],
        "max": summary["max"],
    }


def export_json(results: List[BatchResult]) -> str:
    """Serialize a list of BatchResults to a JSON string."""
    data = [_build_row(br) for br in results]
    return json.dumps(data, indent=2)


def export_csv(results: List[BatchResult]) -> str:
    """Serialize a list of BatchResults to a CSV string."""
    fieldnames = ["label", "iterations", "success_count", "mean", "median", "stdev", "min", "max"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for br in results:
        writer.writerow(_build_row(br))
    return output.getvalue()


def export(results: List[BatchResult], fmt: str) -> str:
    """Export results in the given format ('json' or 'csv')."""
    if fmt == "json":
        return export_json(results)
    elif fmt == "csv":
        return export_csv(results)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")
