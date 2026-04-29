"""CLI entry-point for the interpolator module."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.interpolator import interpolate, format_interpolate_summary


def _load_batches(path: str) -> List[BatchResult]:
    with open(path) as fh:
        data = json.load(fh)
    batches: List[BatchResult] = []
    for item in data:
        runs = [
            RunResult(
                command=r.get("command", ""),
                elapsed=float(r["elapsed"]),
                returncode=int(r.get("returncode", 0)),
                stdout=r.get("stdout", ""),
                stderr=r.get("stderr", ""),
            )
            for r in item.get("runs", [])
        ]
        batches.append(BatchResult(label=item["label"], runs=runs))
    return batches


def build_interpolate_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-interpolate",
        description="Interpolate missing data points in benchmark run sets.",
    )
    p.add_argument("input", help="JSON file produced by batchmark export")
    p.add_argument(
        "--target", type=int, default=10,
        help="Target number of runs per batch (default: 10)",
    )
    p.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )
    return p


def main(argv=None) -> None:
    parser = build_interpolate_parser()
    args = parser.parse_args(argv)

    try:
        batches = _load_batches(args.input)
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        result = interpolate(batches, args.target)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        out = [
            {
                "label": b.label,
                "total": b.total,
                "added": b.added_count,
                "runs": [{"elapsed": r.elapsed, "returncode": r.returncode} for r in b.runs],
            }
            for b in result.batches
        ]
        print(json.dumps(out, indent=2))
    else:
        print(format_interpolate_summary(result))


if __name__ == "__main__":  # pragma: no cover
    main()
