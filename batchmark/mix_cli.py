"""mix_cli.py — CLI entry-point for the mixer feature."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List

from batchmark.runner import BatchResult, RunResult
from batchmark.mixer import mix, format_mix_summary
from batchmark.exporter import export_json


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


def build_mix_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-mix",
        description="Mix runs from multiple benchmark result files.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="JSON result files to mix (use name=file.json to set source name)",
    )
    p.add_argument(
        "--ratio",
        type=float,
        default=None,
        metavar="R",
        help="Fraction of runs to keep per label (0 < R <= 1)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible sampling",
    )
    p.add_argument(
        "--labels",
        nargs="+",
        default=None,
        metavar="LABEL",
        help="Only include these labels in output",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )
    return p


def main(argv=None) -> None:
    parser = build_mix_parser()
    args = parser.parse_args(argv)

    sources: Dict[str, List[BatchResult]] = {}
    for spec in args.files:
        if "=" in spec:
            name, path = spec.split("=", 1)
        else:
            name = spec
            path = spec
        try:
            sources[name] = _load_batches(path)
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            sys.exit(1)

    try:
        result = mix(sources, ratio=args.ratio, seed=args.seed, labels=args.labels)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        batches = [
            BatchResult(label=mb.label, runs=mb.runs) for mb in result.batches
        ]
        print(export_json(batches))
    else:
        print(format_mix_summary(result))
