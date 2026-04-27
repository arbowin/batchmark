"""trim_cli.py — CLI entry point for the trimmer module."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.trimmer import format_trim_summary, trim_all


def build_trim_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-trim",
        description="Trim outlier runs from benchmark results by percentile bounds.",
    )
    parser.add_argument("input", help="Path to JSON file containing batch results")
    parser.add_argument(
        "--lower", type=float, default=5.0, metavar="PCT",
        help="Lower percentile cutoff (default: 5.0)",
    )
    parser.add_argument(
        "--upper", type=float, default=95.0, metavar="PCT",
        help="Upper percentile cutoff (default: 95.0)",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Write trimmed JSON results to this file instead of stdout",
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Print a human-readable trim summary to stderr",
    )
    return parser


def _load_batches(path: str) -> List[BatchResult]:
    with open(path) as fh:
        data = json.load(fh)
    batches = []
    for item in data:
        runs = [
            RunResult(elapsed=r["elapsed"], returncode=r["returncode"], stdout=r.get("stdout", ""), stderr=r.get("stderr", ""))
            for r in item["runs"]
        ]
        batches.append(BatchResult(label=item["label"], runs=runs))
    return batches


def main(argv: List[str] | None = None) -> None:
    parser = build_trim_parser()
    args = parser.parse_args(argv)

    try:
        batches = _load_batches(args.input)
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        result = trim_all(batches, lower_pct=args.lower, upper_pct=args.upper)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.summary:
        print(format_trim_summary(result), file=sys.stderr)

    output = [
        {
            "label": b.label,
            "runs": [{"elapsed": r.elapsed, "returncode": r.returncode} for r in b.runs],
            "removed_count": b.removed_count,
            "lower_bound": b.lower_bound,
            "upper_bound": b.upper_bound,
        }
        for b in result.batches
    ]

    text = json.dumps(output, indent=2)
    if args.output:
        with open(args.output, "w") as fh:
            fh.write(text)
    else:
        print(text)
