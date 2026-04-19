"""CLI entry point for batchmark."""

import argparse
import sys
from batchmark.runner import benchmark_command
from batchmark.formatter import format_summary, format_table
from batchmark.exporter import export
from batchmark.comparator import compare, format_comparison


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark",
        description="Benchmark batches of shell commands with statistical summaries.",
    )
    parser.add_argument("commands", nargs="+", help="Shell commands to benchmark")
    parser.add_argument("-n", "--iterations", type=int, default=10,
                        help="Number of iterations per command (default: 10)")
    parser.add_argument("--labels", nargs="+", help="Labels for each command")
    parser.add_argument("--export", choices=["json", "csv"], dest="export_format",
                        help="Export results to stdout in given format")
    parser.add_argument("--compare", action="store_true",
                        help="Show side-by-side comparison table when multiple commands given")
    parser.add_argument("--baseline", type=str, default=None,
                        help="Label to use as baseline in comparison (default: fastest)")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    labels = args.labels or args.commands
    if len(labels) != len(args.commands):
        parser.error("--labels count must match number of commands")

    results = []
    for cmd, label in zip(args.commands, labels):
        try:
            br = benchmark_command(cmd, iterations=args.iterations, label=label)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        results.append(br)

    if args.export_format:
        print(export(results, fmt=args.export_format))
        return

    if args.compare and len(results) > 1:
        cmp_result = compare(results, baseline_label=args.baseline)
        print(format_comparison(cmp_result))
    else:
        summaries = [format_summary(br) for br in results]
        print(format_table(summaries))


if __name__ == "__main__":
    main()
