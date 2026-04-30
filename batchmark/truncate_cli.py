"""CLI entry point for the truncator module."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.truncator import format_truncate_summary, truncate


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


def build_truncate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-truncate",
        description="Truncate batch runs to a fixed maximum count.",
    )
    parser.add_argument("input", help="JSON file with batch results")
    parser.add_argument(
        "--max-runs",
        type=int,
        default=10,
        dest="max_runs",
        help="Maximum number of runs to keep per batch (default: 10)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="format",
        help="Output format (default: text)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_truncate_parser()
    args = parser.parse_args(argv)

    try:
        batches = _load_batches(args.input)
        result = truncate(batches, args.max_runs)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        output = [
            {
                "label": tb.label,
                "total": tb.total,
                "success_count": tb.success_count,
                "runs": [
                    {"elapsed": r.elapsed, "returncode": r.returncode}
                    for r in tb.runs
                ],
            }
            for tb in result.batches
        ]
        print(json.dumps(output, indent=2))
    else:
        print(format_truncate_summary(result))


if __name__ == "__main__":  # pragma: no cover
    main()
