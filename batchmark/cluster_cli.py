"""CLI entry point for the clusterizer feature."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.runner import BatchResult, RunResult
from batchmark.clusterizer import clusterize, format_clusters


def build_cluster_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-cluster",
        description="Cluster benchmark results by elapsed-time similarity.",
    )
    parser.add_argument(
        "input",
        help="Path to JSON file containing benchmark results (list of BatchResult dicts).",
    )
    parser.add_argument(
        "-k",
        "--clusters",
        type=int,
        default=3,
        metavar="K",
        help="Number of clusters (default: 3).",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=100,
        dest="max_iter",
        help="Maximum k-means iterations (default: 100).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON instead of plain text.",
    )
    return parser


def _load_batches(path: str) -> List[BatchResult]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    batches = []
    for item in data:
        runs = [
            RunResult(
                elapsed=r.get("elapsed"),
                returncode=r.get("returncode", 0),
                stdout=r.get("stdout", ""),
                stderr=r.get("stderr", ""),
            )
            for r in item.get("runs", [])
        ]
        batches.append(BatchResult(label=item["label"], runs=runs))
    return batches


def main(argv: list | None = None) -> None:
    parser = build_cluster_parser()
    args = parser.parse_args(argv)

    try:
        batches = _load_batches(args.input)
    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        result = clusterize(batches, k=args.clusters, max_iter=args.max_iter)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        output = [
            {
                "cluster": i + 1,
                "centroid": cluster.centroid,
                "members": cluster.labels,
            }
            for i, cluster in enumerate(result.clusters)
        ]
        print(json.dumps(output, indent=2))
    else:
        print(format_clusters(result))


if __name__ == "__main__":  # pragma: no cover
    main()
