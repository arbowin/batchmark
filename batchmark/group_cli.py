"""CLI entry point for the grouper feature."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.grouper import (
    format_grouped,
    group_by_label,
    group_by_prefix,
)


def build_group_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-group",
        description="Group benchmark results by label or prefix.",
    )
    parser.add_argument(
        "input",
        help="Path to a JSON file produced by batchmark export (or '-' for stdin).",
    )
    parser.add_argument(
        "--strategy",
        choices=["label", "prefix"],
        default="prefix",
        help="Grouping strategy (default: prefix).",
    )
    parser.add_argument(
        "--sep",
        default=":",
        help="Separator used for prefix grouping (default: ':').",
    )
    return parser


def _load_batches(path: str) -> List[BatchResult]:
    if path == "-":
        data = json.load(sys.stdin)
    else:
        with open(path) as fh:
            data = json.load(fh)
    batches: List[BatchResult] = []
    for entry in data:
        runs = [
            RunResult(elapsed=r["elapsed"], returncode=r["returncode"])
            for r in entry.get("runs", [])
        ]
        batches.append(BatchResult(label=entry["label"], runs=runs))
    return batches


def main(argv: list[str] | None = None) -> None:
    parser = build_group_parser()
    args = parser.parse_args(argv)

    try:
        batches = _load_batches(args.input)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not batches:
        print("No batches found.", file=sys.stderr)
        sys.exit(1)

    if args.strategy == "label":
        grouped = group_by_label(batches)
    else:
        grouped = group_by_prefix(batches, sep=args.sep)

    print(format_grouped(grouped))
