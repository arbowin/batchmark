"""CLI entry-point for the pivot sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.pivotter import pivot, format_pivot, _METRICS


def _load_batches(path: str) -> List[BatchResult]:
    with open(path) as fh:
        data = json.load(fh)
    batches = []
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


def build_pivot_parser(sub: "argparse._SubParsersAction | None" = None) -> argparse.ArgumentParser:  # noqa: F821
    kwargs = dict(description="Pivot benchmark results by label and metric")
    parser = sub.add_parser("pivot", **kwargs) if sub else argparse.ArgumentParser(**kwargs)
    parser.add_argument("input", help="JSON file produced by batchmark export")
    parser.add_argument(
        "--metrics",
        nargs="+",
        choices=list(_METRICS),
        default=None,
        metavar="METRIC",
        help="Metrics to include (default: all)",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=4,
        help="Decimal places in output (default: 4)",
    )
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_pivot_parser()
    args = parser.parse_args(argv)
    try:
        batches = _load_batches(args.input)
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not batches:
        print("error: no batches found in input", file=sys.stderr)
        sys.exit(1)
    result = pivot(batches, metrics=args.metrics)
    print(format_pivot(result, precision=args.precision))


if __name__ == "__main__":  # pragma: no cover
    main()
