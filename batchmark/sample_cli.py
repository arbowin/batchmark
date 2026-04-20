"""sample_cli.py — CLI entry-point for the sampler module."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.sampler import sample_all
from batchmark.stats import summarize


def build_sample_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-sample",
        description="Sample runs from benchmark results and print a summary.",
    )
    p.add_argument(
        "input",
        help="JSON file produced by batchmark export (list of batch objects).",
    )
    p.add_argument(
        "-k", "--size",
        type=int,
        default=10,
        metavar="K",
        help="Number of runs to sample per batch (default: 10).",
    )
    p.add_argument(
        "--strategy",
        choices=["reservoir", "systematic"],
        default="reservoir",
        help="Sampling strategy (default: reservoir).",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reservoir sampling.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit results as JSON instead of plain text.",
    )
    return p


def _batches_from_json(path: str) -> List[BatchResult]:
    with open(path) as fh:
        data = json.load(fh)
    batches: List[BatchResult] = []
    for obj in data:
        runs = [
            RunResult(
                elapsed=r["elapsed"],
                returncode=r["returncode"],
                stdout=r.get("stdout", ""),
                stderr=r.get("stderr", ""),
            )
            for r in obj.get("runs", [])
        ]
        batches.append(BatchResult(label=obj["label"], runs=runs))
    return batches


def main(argv: list[str] | None = None) -> None:
    parser = build_sample_parser()
    args = parser.parse_args(argv)

    try:
        batches = _batches_from_json(args.input)
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"error: invalid input file — {exc}", file=sys.stderr)
        sys.exit(1)

    sampled = sample_all(batches, k=args.size, strategy=args.strategy, seed=args.seed)

    if args.json:
        out = [
            {
                "label": sb.label,
                "strategy": sb.strategy,
                "original_count": sb.original_count,
                "sample_size": sb.sample_size,
                "runs": [{"elapsed": r.elapsed, "returncode": r.returncode} for r in sb.runs],
            }
            for sb in sampled
        ]
        print(json.dumps(out, indent=2))
    else:
        for sb in sampled:
            times = [r.elapsed for r in sb.runs]
            stats = summarize(times)
            print(
                f"{sb.label}: sampled {sb.sample_size}/{sb.original_count} "
                f"({sb.strategy})  mean={stats['mean']:.4f}s  "
                f"median={stats['median']:.4f}s  stdev={stats['stdev']:.4f}s"
            )


if __name__ == "__main__":  # pragma: no cover
    main()
