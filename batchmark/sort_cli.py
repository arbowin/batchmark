"""CLI entry point for the sort subcommand."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.sorter import SortKey, SortOrder, format_sort_result, sort_batches


def build_sort_parser(sub: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    parser = sub or argparse.ArgumentParser(
        prog="batchmark sort",
        description="Sort benchmark results by a chosen metric.",
    )
    parser.add_argument("file", help="JSON file produced by batchmark export")
    parser.add_argument(
        "--key",
        choices=["mean", "median", "label", "success_rate", "total"],
        default="mean",
        help="Metric to sort by (default: mean)",
    )
    parser.add_argument(
        "--order",
        choices=["asc", "desc"],
        default="asc",
        help="Sort direction (default: asc)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit sorted results as JSON",
    )
    return parser


def _load_batches(path: str) -> List[BatchResult]:
    with open(path) as fh:
        data = json.load(fh)
    batches: List[BatchResult] = []
    for entry in data:
        runs = [
            RunResult(
                elapsed=r["elapsed"],
                returncode=r["returncode"],
                stdout=r.get("stdout", ""),
                stderr=r.get("stderr", ""),
            )
            for r in entry.get("runs", [])
        ]
        batches.append(BatchResult(label=entry["label"], runs=runs))
    return batches


def main(argv: list[str] | None = None) -> None:
    parser = build_sort_parser()
    args = parser.parse_args(argv)

    try:
        batches = _load_batches(args.file)
        result = sort_batches(batches, key=args.key, order=args.order)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json_output:
        out = [
            {"label": b.label, "runs": [{"elapsed": r.elapsed, "returncode": r.returncode} for r in b.runs]}
            for b in result.batches
        ]
        print(json.dumps(out, indent=2))
    else:
        print(format_sort_result(result))
