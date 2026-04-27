"""CLI entry-point for sliding-window analysis."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.windower import format_window_result, slide


def build_window_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-window",
        description="Sliding-window statistics over a sequence of benchmark snapshots.",
    )
    p.add_argument("input", help="JSON file produced by batchmark export (list of batch objects)")
    p.add_argument(
        "--window", "-w", type=int, default=3, metavar="N", help="Window size (default: 3)"
    )
    p.add_argument(
        "--label", "-l", action="append", dest="labels", metavar="LABEL",
        help="Restrict output to these labels (repeatable)",
    )
    p.add_argument(
        "--json", dest="json_out", action="store_true", help="Output raw JSON instead of text"
    )
    return p


def _load_batches(path: str) -> List[BatchResult]:
    with open(path) as fh:
        data = json.load(fh)
    batches: List[BatchResult] = []
    for obj in data:
        runs = [
            RunResult(elapsed=r["elapsed"], returncode=r["returncode"], stdout=r.get("stdout", ""), stderr=r.get("stderr", ""))
            for r in obj.get("runs", [])
        ]
        batches.append(BatchResult(label=obj["label"], runs=runs))
    return batches


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = build_window_parser()
    args = parser.parse_args(argv)

    try:
        batches = _load_batches(args.input)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.labels:
        batches = [b for b in batches if b.label in args.labels]

    if not batches:
        print("error: no batches to analyse", file=sys.stderr)
        sys.exit(1)

    try:
        results = slide(batches, args.window)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json_out:
        out = []
        for wr in results:
            out.append({
                "label": wr.label,
                "window_size": wr.window_size,
                "windows": [
                    {"start": w.start, "end": w.end, "mean": w.mean,
                     "stdev": w.stdev, "run_count": w.run_count,
                     "success_count": w.success_count}
                    for w in wr.windows
                ],
            })
        print(json.dumps(out, indent=2))
    else:
        for wr in results:
            print(format_window_result(wr))
            print()
