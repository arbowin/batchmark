"""mix_export.py — serialisation helpers for MixResult."""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List

from batchmark.mixer import MixedBatch, MixResult
from batchmark.stats import mean, stdev


def _batch_to_dict(mb: MixedBatch) -> Dict[str, Any]:
    times = [r.elapsed for r in mb.runs]
    return {
        "label": mb.label,
        "sources": mb.sources,
        "total": mb.total,
        "success_count": mb.success_count,
        "mean": mean(times) if times else None,
        "stdev": stdev(times) if len(times) > 1 else None,
        "runs": [
            {"elapsed": r.elapsed, "returncode": r.returncode}
            for r in mb.runs
        ],
    }


def export_mix_json(result: MixResult, *, indent: int = 2) -> str:
    """Serialise a MixResult to a JSON string."""
    return json.dumps([_batch_to_dict(mb) for mb in result.batches], indent=indent)


def export_mix_csv(result: MixResult) -> str:
    """Serialise a MixResult to a CSV string (one row per MixedBatch)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["label", "sources", "total", "success_count", "mean", "stdev"])
    for mb in result.batches:
        times = [r.elapsed for r in mb.runs]
        writer.writerow([
            mb.label,
            "|".join(mb.sources),
            mb.total,
            mb.success_count,
            f"{mean(times):.6f}" if times else "",
            f"{stdev(times):.6f}" if len(times) > 1 else "",
        ])
    return buf.getvalue()


def save_mix_export(result: MixResult, path: str, *, fmt: str = "json") -> None:
    """Write a MixResult to *path* in the requested format ('json' or 'csv')."""
    if fmt == "json":
        content = export_mix_json(result)
    elif fmt == "csv":
        content = export_mix_csv(result)
    else:
        raise ValueError(f"unsupported format: {fmt!r}")
    with open(path, "w", newline="") as fh:
        fh.write(content)
