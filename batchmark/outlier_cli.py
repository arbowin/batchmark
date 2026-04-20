"""CLI entry-point for outlier detection on benchmark results."""

import argparse
import sys
from batchmark.runner import benchmark_command
from batchmark.outlier import detect_outliers, format_outlier_report


def build_outlier_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-outliers",
        description="Detect outliers in benchmark run times.",
    )
    parser.add_argument(
        "commands",
        nargs="+",
        help="Shell commands to benchmark.",
    )
    parser.add_argument(
        "-n", "--iterations",
        type=int,
        default=20,
        help="Number of iterations per command (default: 20).",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        metavar="LABEL",
        help="Optional labels for each command (must match command count).",
    )
    parser.add_argument(
        "--method",
        choices=["iqr", "zscore"],
        default="iqr",
        help="Outlier detection method (default: iqr).",
    )
    parser.add_argument(
        "--z-threshold",
        type=float,
        default=2.5,
        dest="z_threshold",
        help="Z-score threshold when using zscore method (default: 2.5).",
    )
    return parser


def main(argv=None) -> None:
    parser = build_outlier_parser()
    args = parser.parse_args(argv)

    if args.labels and len(args.labels) != len(args.commands):
        parser.error(
            f"Number of labels ({len(args.labels)}) must match "
            f"number of commands ({len(args.commands)})."
        )

    labels = args.labels or args.commands

    any_outliers = False
    for cmd, label in zip(args.commands, labels):
        batch = benchmark_command(cmd, iterations=args.iterations, label=label)
        result = detect_outliers(
            batch, method=args.method, z_threshold=args.z_threshold
        )
        if result is None:
            print(
                f"[{label}] Not enough data points for outlier detection "
                f"(need >= 4, got {args.iterations})."
            )
            continue
        print(format_outlier_report(result))
        print()
        if result.has_outliers:
            any_outliers = True

    sys.exit(1 if any_outliers else 0)


if __name__ == "__main__":  # pragma: no cover
    main()
