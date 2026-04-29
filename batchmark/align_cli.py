"""CLI entry-point for the align sub-command.

Usage example::

    batchmark-align snapshot_a.json snapshot_b.json \\
        --names run-A run-B \\
        --no-fill
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.aligner import align, format_alignment


def _load_batches(path: str) -> List[BatchResult]:
    """Load a JSON file produced by batchmark's snapshot/export tooling."""
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
            for r in entry.get("runs", [])
        ]
        batches.append(BatchResult(label=entry["label"], runs=runs))
    return batches


def build_align_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-align",
        description="Align multiple benchmark result sets to a common label space.",
    )
    p.add_argument(
        "sources",
        nargs="+",
        metavar="FILE",
        help="JSON result files to align (at least one required).",
    )
    p.add_argument(
        "--names",
        nargs="+",
        metavar="NAME",
        default=None,
        help="Human-readable name for each source file (must match count).",
    )
    p.add_argument(
        "--no-fill",
        dest="fill_missing",
        action="store_false",
        default=True,
        help="Do not insert placeholder entries for missing labels.",
    )
    p.add_argument(
        "--common-only",
        action="store_true",
        default=False,
        help="Print only labels present in every source.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_align_parser()
    args = parser.parse_args(argv)

    if args.names and len(args.names) != len(args.sources):
        parser.error(
            f"--names expects {len(args.sources)} value(s), "
            f"got {len(args.names)}."
        )

    sources = []
    for path in args.sources:
        try:
            sources.append(_load_batches(path))
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            sys.exit(1)

    result = align(sources, names=args.names, fill_missing=args.fill_missing)

    if args.common_only:
        print("Common labels: " + ", ".join(result.common_labels))
    else:
        print(format_alignment(result))


if __name__ == "__main__":  # pragma: no cover
    main()
