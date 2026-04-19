"""Export benchmark results to JSON or CSV formats."""

import csv
import json
import io
from typing import List
from batchmark.runner import BatchResult
from batchmark.stats import summarize


def export_json(results: List[BatchResult]) -> str:
    """Serialize a list of BatchResults to a JSON string."""
    data = []
    for br in results:
        summary = summarize(br)
        data.append({
            "label": br.label,
            "iterations": len(br.times),
            "success_count": br.success_count,
            "mean": summary["mean"],
            "median": summary["median"],
            "stdev": summary["stdev"],
            "min": summary["min"],
            "max": summary["max"],
        })
    return json.dumps(data, indent=2)


def export_csv(results: List[BatchResult]) -> str:
    """Serialize a list of BatchResults to a CSV string."""
    fieldnames = ["label", "iterations", "success_count", "mean", "median", "stdev", "min", "max"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for br in results:
        summary = summarize(br)
        writer.writerow({
            "label": br.label,
            "iterations": len(br.times),
            "success_count": br.success_count,
            "mean": summary["mean"],
            "median": summary["median"],
            "stdev": summary["stdev"],
            "min": summary["min"],
            "max": summary["max"],
        })
    return output.getvalue()


def export(results: List[BatchResult], fmt: str) -> str:
    """Export results in the given format ('json' or 'csv')."""
    if fmt == "json":
        return export_json(results)
    elif fmt == "csv":
        return export_csv(results)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")
