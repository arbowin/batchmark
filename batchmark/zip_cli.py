"""CLI entry-point for the zipper feature."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.zipper import format_zip, zip_batches


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


def build_zip_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-zip",
        description="Zip two sets of benchmark results by label.",
    )
    p.add_argument("left", help="Path to left JSON results file.")
    p.add_argument("right", help="Path to right JSON results file.")
    p.add_argument("--left-name", default="left", help="Display name for left set.")
    p.add_argument("--right-name", default="right", help="Display name for right set.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    return p


def main(argv: List[str] | None = None) -> None:
    parser = build_zip_parser()
    args = parser.parse_args(argv)

    left_batches = _load_batches(args.left)
    right_batches = _load_batches(args.right)

    result = zip_batches(left_batches, right_batches)

    if args.format == "json":
        out = [
            {
                "label": p.label,
                "left_mean": p.left_mean,
                "right_mean": p.right_mean,
                "delta": p.delta,
                "ratio": p.ratio,
            }
            for p in result.pairs
        ]
        print(json.dumps(out, indent=2))
    else:
        print(format_zip(result, left_name=args.left_name, right_name=args.right_name))

    if result.left_only or result.right_only:
        sys.exit(1)


if __name__ == "__main__":
    main()
