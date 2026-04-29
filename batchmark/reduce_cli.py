"""reduce_cli.py – CLI entry-point for the reducer module.

Usage example:
  batchmark-reduce --files run1.json run2.json --strategy mean
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.reducer import reduce, format_reduced


def build_reduce_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-reduce",
        description="Reduce multiple benchmark result files into a single representative batch.",
    )
    p.add_argument(
        "--files",
        nargs="+",
        required=True,
        metavar="FILE",
        help="JSON files produced by batchmark (one per benchmark run).",
    )
    p.add_argument(
        "--strategy",
        choices=["mean", "median"],
        default="mean",
        help="Aggregation strategy (default: mean).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    return p


def _load_source(path: str) -> List[BatchResult]:
    """Load a JSON file as a list of BatchResult objects."""
    with open(path) as fh:
        data = json.load(fh)
    batches: List[BatchResult] = []
    for item in data:
        runs = [
            RunResult(
                elapsed=r["elapsed"],
                returncode=r["returncode"],
                stdout=r.get("stdout", ""),
                stderr=r.get("stderr", ""),
            )
            for r in item["runs"]
        ]
        batches.append(BatchResult(label=item["label"], runs=runs))
    return batches


def main(argv: list[str] | None = None) -> None:
    parser = build_reduce_parser()
    args = parser.parse_args(argv)

    sources = []
    for path in args.files:
        try:
            sources.append(_load_source(path))
        except (OSError, KeyError, json.JSONDecodeError) as exc:
            print(f"error: could not load {path!r}: {exc}", file=sys.stderr)
            sys.exit(1)

    try:
        result = reduce(sources, strategy=args.strategy)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output_format == "json":
        payload = [
            {
                "label": b.label,
                "strategy": b.strategy,
                "source_count": b.source_count,
                "elapsed": b.runs[0].elapsed,
                "returncode": b.runs[0].returncode,
            }
            for b in result.batches
        ]
        print(json.dumps(payload, indent=2))
    else:
        print(format_reduced(result))
