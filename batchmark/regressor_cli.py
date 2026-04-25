"""CLI entry-point for the regression detector."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

from batchmark.runner import BatchResult, RunResult
from batchmark.regressor import detect_regressions, format_regression_report


def build_regressor_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-regress",
        description="Detect regressions by comparing current results to a baseline.",
    )
    p.add_argument("baseline", help="Path to baseline JSON file (label -> mean_s).")
    p.add_argument("current", help="Path to current snapshot JSON file.")
    p.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        metavar="PCT",
        help="Percentage change to classify as regression/improvement (default: 5.0).",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if any regressions are found.",
    )
    return p


def _load_baseline(path: str) -> Dict[str, float]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError("Baseline JSON must be a mapping of label -> mean_s.")
    return {k: float(v) for k, v in data.items()}


def _load_current(path: str) -> List[BatchResult]:
    raw = json.loads(Path(path).read_text())
    batches: List[BatchResult] = []
    for item in raw:
        runs = [
            RunResult(elapsed=r["elapsed"], returncode=r["returncode"])
            for r in item.get("runs", [])
        ]
        batches.append(BatchResult(label=item["label"], runs=runs))
    return batches


def main(argv: List[str] | None = None) -> None:
    parser = build_regressor_parser()
    args = parser.parse_args(argv)

    try:
        baseline = _load_baseline(args.baseline)
        current = _load_current(args.current)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"Error loading input files: {exc}", file=sys.stderr)
        sys.exit(2)

    report = detect_regressions(baseline, current, threshold_pct=args.threshold)
    print(format_regression_report(report))

    if args.exit_code and report.regressions():
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
