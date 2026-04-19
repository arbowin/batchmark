"""CLI entry point for batchmark."""

import argparse
import sys

from batchmark.runner import benchmark_command
from batchmark.formatter import format_summary, format_table


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark",
        description="Benchmark batches of shell commands with statistical summaries.",
    )
    parser.add_argument(
        "commands",
        nargs="+",
        metavar="CMD",
        help="Shell command(s) to benchmark.",
    )
    parser.add_argument(
        "-n", "--iterations",
        type=int,
        default=10,
        metavar="N",
        help="Number of iterations per command (default: 10).",
    )
    parser.add_argument(
        "--table",
        action="store_true",
        help="Display results as a comparison table.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.iterations < 1:
        print("error: iterations must be at least 1", file=sys.stderr)
        return 1

    results = {}
    for cmd in args.commands:
        print(f"Benchmarking: {cmd} ...", file=sys.stderr)
        try:
            results[cmd] = benchmark_command(cmd, iterations=args.iterations)
        except Exception as exc:  # noqa: BLE001
            print(f"error running '{cmd}': {exc}", file=sys.stderr)
            return 1

    if args.table:
        print(format_table(results))
    else:
        for label, result in results.items():
            print(format_summary(label, result))
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
