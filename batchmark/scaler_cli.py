"""CLI entry point for scaling batch run times."""

import argparse
import json
import sys
from pathlib import Path

from batchmark.runner import BatchResult, RunResult
from batchmark.scaler import scale_all, format_scale_summary


def _load_batches(path: str) -> list[BatchResult]:
    raw = json.loads(Path(path).read_text())
    batches = []
    for item in raw:
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


def build_scale_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-scale",
        description="Scale batch run times by a factor or offset.",
    )
    parser.add_argument("input", help="JSON file containing batch results")
    parser.add_argument(
        "--factor",
        type=float,
        default=1.0,
        help="Multiplicative scale factor (default: 1.0)",
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="Additive offset applied after factor (default: 0.0)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=4,
        help="Decimal precision for text output (default: 4)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_scale_parser()
    args = parser.parse_args(argv)

    batches = _load_batches(args.input)
    result = scale_all(batches, factor=args.factor, offset=args.offset)

    if args.format == "json":
        out = [
            {
                "label": sb.label,
                "runs": [
                    {"elapsed": r.elapsed, "returncode": r.returncode}
                    for r in sb.runs
                ],
            }
            for sb in result.batches
        ]
        print(json.dumps(out, indent=2))
    else:
        print(format_scale_summary(result, precision=args.precision))


if __name__ == "__main__":
    main()
