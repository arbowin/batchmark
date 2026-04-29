"""Export ZipResult to JSON or CSV."""

from __future__ import annotations

import csv
import io
import json
from typing import List

from batchmark.zipper import ZipResult, ZippedPair


def _pair_to_dict(pair: ZippedPair) -> dict:
    return {
        "label": pair.label,
        "left_mean": pair.left_mean,
        "right_mean": pair.right_mean,
        "left_stdev": pair.left_stdev,
        "right_stdev": pair.right_stdev,
        "left_success": pair.left_success,
        "right_success": pair.right_success,
        "left_total": pair.left_total,
        "right_total": pair.right_total,
        "delta": pair.delta,
        "ratio": pair.ratio,
    }


def export_zip_json(result: ZipResult) -> str:
    """Serialise ZipResult pairs to a JSON string."""
    payload = {
        "pairs": [_pair_to_dict(p) for p in result.pairs],
        "left_only": result.left_only,
        "right_only": result.right_only,
    }
    return json.dumps(payload, indent=2)


def export_zip_csv(result: ZipResult) -> str:
    """Serialise ZipResult pairs to a CSV string."""
    buf = io.StringIO()
    fieldnames = [
        "label",
        "left_mean",
        "right_mean",
        "left_stdev",
        "right_stdev",
        "left_success",
        "right_success",
        "left_total",
        "right_total",
        "delta",
        "ratio",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for pair in result.pairs:
        writer.writerow(_pair_to_dict(pair))
    return buf.getvalue()


def save_zip_export(result: ZipResult, path: str, fmt: str = "json") -> None:
    """Write ZipResult to *path* in the requested format ('json' or 'csv')."""
    if fmt == "csv":
        content = export_zip_csv(result)
    else:
        content = export_zip_json(result)
    with open(path, "w") as fh:
        fh.write(content)
