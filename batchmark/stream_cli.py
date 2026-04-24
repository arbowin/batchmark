"""CLI entry-point for streaming benchmark results."""

from __future__ import annotations

import argparse
import sys

from batchmark.formatter import format_summary
from batchmark.streamer import StreamConfig, collect_stream


def build_stream_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-stream",
        description="Benchmark commands and stream results as each one completes.",
    )
    parser.add_argument(
        "commands",
        nargs="+",
        help="Shell commands to benchmark.",
    )
    parser.add_argument(
        "-l", "--labels",
        nargs="+",
        default=None,
        help="Labels for each command (must match command count).",
    )
    parser.add_argument(
        "-n", "--iterations",
        type=int,
        default=5,
        help="Number of iterations per command (default: 5).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-result output; only print final summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_stream_parser()
    args = parser.parse_args(argv)

    labels = args.labels if args.labels else args.commands
    if len(labels) != len(args.commands):
        print("error: number of labels must match number of commands", file=sys.stderr)
        sys.exit(1)

    def _on_result(result) -> None:
        if not args.quiet:
            print(format_summary(result))

    config = StreamConfig(
        commands=args.commands,
        labels=labels,
        iterations=args.iterations,
        on_result=_on_result,
    )

    session = collect_stream(config)
    print(f"\nStreamed {session.completed}/{session.total} commands.")


if __name__ == "__main__":
    main()
