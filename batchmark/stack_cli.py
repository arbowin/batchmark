"""CLI entry point for the stacker module."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List

from batchmark.runner import BatchResult, RunResult
from batchmark.stacker import format_stack, stack


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
            for r in entry["runs"]
        ]
        batches.append(BatchResult(label=entry["label"], runs=runs))
    return batches


def build_stack_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-stack",
        description="Stack multiple benchmark result files for side-by-side comparison.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="JSON result files to stack (use name=file.json to set source name)",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=4,
        help="Decimal places for timing values (default: 4)",
    )
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_stack_parser()
    args = parser.parse_args(argv)

    sources: Dict[str, List[BatchResult]] = {}
    for token in args.files:
        if "=" in token:
            name, path = token.split("=", 1)
        else:
            name = token
            path = token
        try:
            sources[name] = _load_batches(path)
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            sys.exit(1)

    try:
        result = stack(sources)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(format_stack(result, precision=args.precision))


if __name__ == "__main__":  # pragma: no cover
    main()
