"""CLI entry-point for the smoother module."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.smoother import format_smooth, smooth


def build_smooth_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-smooth",
        description="Apply rolling-average smoothing to batch timing series.",
    )
    parser.add_argument(
        "input",
        metavar="FILE",
        help="JSON file produced by batchmark export (list of batch objects).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=5,
        metavar="N",
        help="Runs per raw data point (default: 5).",
    )
    parser.add_argument(
        "--span",
        type=int,
        default=3,
        metavar="N",
        help="Rolling-average window width (default: 3).",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        metavar="LABEL",
        help="Only process batches with these labels.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of plain text.",
    )
    return parser


def _load_batches(path: str) -> List[BatchResult]:
    with open(path, encoding="utf-8") as fh:
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
            for r in item.get("results", [])
        ]
        batches.append(BatchResult(label=item["label"], results=runs))
    return batches


def main(argv: list[str] | None = None) -> None:
    parser = build_smooth_parser()
    args = parser.parse_args(argv)

    try:
        batches = _load_batches(args.input)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.labels:
        batches = [b for b in batches if b.label in args.labels]
        if not batches:
            print("error: no batches matched the provided labels.", file=sys.stderr)
            sys.exit(1)

    try:
        result = smooth(batches, chunk_size=args.chunk_size, span=args.span)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        output = [
            {
                "label": sb.label,
                "points": [
                    {
                        "index": p.index,
                        "raw_mean": p.raw_mean,
                        "smoothed_mean": p.smoothed_mean,
                    }
                    for p in sb.points
                ],
            }
            for sb in result.batches
        ]
        print(json.dumps(output, indent=2))
    else:
        print(format_smooth(result))


if __name__ == "__main__":  # pragma: no cover
    main()
