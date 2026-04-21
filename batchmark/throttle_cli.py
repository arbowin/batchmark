"""CLI entry-point for throttled benchmarking."""

from __future__ import annotations

import argparse
import sys

from batchmark.runner import benchmark_command
from batchmark.throttler import ThrottleConfig, format_throttle_summary, throttle_benchmark
from batchmark.formatter import format_summary
from batchmark.stats import summarize


def build_throttle_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-throttle",
        description="Run a benchmark with rate-limiting between iterations.",
    )
    parser.add_argument("command", help="Shell command to benchmark")
    parser.add_argument("-l", "--label", default="", help="Label for this benchmark")
    parser.add_argument(
        "-n", "--iterations", type=int, default=10,
        help="Total number of iterations (default: 10)",
    )
    parser.add_argument(
        "--burst", type=int, default=1,
        help="Runs per burst before cooldown (default: 1)",
    )
    parser.add_argument(
        "--delay", type=float, default=0.5,
        help="Seconds to pause between bursts (default: 0.5)",
    )
    parser.add_argument(
        "--cooldown", type=float, default=0.0,
        help="Extra cooldown seconds after each burst (default: 0.0)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_throttle_parser()
    args = parser.parse_args(argv)

    label = args.label or args.command
    config = ThrottleConfig(
        delay_seconds=args.delay,
        burst=args.burst,
        cooldown_seconds=args.cooldown,
    )

    try:
        result = throttle_benchmark(
            command=args.command,
            label=label,
            iterations=args.iterations,
            config=config,
            benchmark_fn=benchmark_command,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    summary = summarize(result.batch)
    print(format_summary(summary))
    print()
    print(format_throttle_summary(result))


if __name__ == "__main__":  # pragma: no cover
    main()
