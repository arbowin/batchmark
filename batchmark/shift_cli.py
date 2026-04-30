"""shift_cli.py — CLI entry point for the shifter module."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.shifter import format_shift_summary, shift_all


def _load_batches(path: str) -> List[BatchResult]:
    with open(path) as fh:
        data = json.load(fh)
    batches: List[BatchResult] = []
    for entry in data:
        runs = [
            RunResult(
                command=r["command"],
                elapsed=r["elapsed"],
                returncode=r["returncode"],
                stdout=r.get("stdout", ""),
                stderr=r.get("stderr", ""),
            )
            for r in entry["runs"]
        ]
        batches.append(BatchResult(label=entry["label"], runs=runs))
    return batches


def build_shift_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-shift",
        description="Shift or scale elapsed times in benchmark batches.",
    )
    p.add_argument("input", help="JSON file produced by batchmark export")
    p.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="Constant seconds to add to every elapsed time (default: 0.0)",
    )
    p.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Multiplicative factor applied before adding offset (default: 1.0)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--precision",
        type=int,
        default=4,
        help="Decimal places for text output (default: 4)",
    )
    return p


def main(argv=None) -> None:
    parser = build_shift_parser()
    args = parser.parse_args(argv)

    try:
        batches = _load_batches(args.input)
        result = shift_all(batches, offset=args.offset, scale=args.scale)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.fmt == "json":
        out = [
            {
                "label": sb.label,
                "runs": [
                    {"command": r.command, "elapsed": r.elapsed, "returncode": r.returncode}
                    for r in sb.runs
                ],
            }
            for sb in result.batches
        ]
        print(json.dumps(out, indent=2))
    else:
        print(format_shift_summary(result, precision=args.precision))


if __name__ == "__main__":  # pragma: no cover
    main()
