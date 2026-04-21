"""CLI entry point for the partitioner module."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.partitioner import (
    partition_by_size,
    partition_by_count,
    format_partition_result,
)


def build_partition_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-partition",
        description="Partition benchmark results into buckets",
    )
    parser.add_argument("input", help="JSON file containing batch results")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--size", type=int, metavar="N", help="Max batches per partition"
    )
    group.add_argument(
        "--count", type=int, metavar="N", help="Number of partitions to create"
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output", help="Output as JSON"
    )
    return parser


def _load_batches(path: str) -> List[BatchResult]:
    with open(path) as fh:
        data = json.load(fh)
    batches: List[BatchResult] = []
    for entry in data:
        runs = [
            RunResult(elapsed=r["elapsed"], returncode=r["returncode"])
            for r in entry["runs"]
        ]
        batches.append(BatchResult(label=entry["label"], runs=runs))
    return batches


def main(argv: List[str] | None = None) -> None:
    parser = build_partition_parser()
    args = parser.parse_args(argv)

    try:
        batches = _load_batches(args.input)
    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.size is not None:
            result = partition_by_size(batches, args.size)
        else:
            result = partition_by_count(batches, args.count)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json_output:
        out = [
            {
                "index": p.index,
                "run_count": p.run_count(),
                "mean": p.mean(),
                "labels": p.labels(),
            }
            for p in result.partitions
        ]
        print(json.dumps(out, indent=2))
    else:
        print(format_partition_result(result))
