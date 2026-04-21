"""CLI entry-point for the replay sub-command."""

import argparse
import sys
from typing import List, Optional

from batchmark.replayer import replay, format_replay


def build_replay_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-replay",
        description="Replay statistical analysis from a saved snapshot.",
    )
    parser.add_argument(
        "snapshot",
        help="Path to the snapshot JSON file.",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        metavar="LABEL",
        default=None,
        help="Limit replay to these labels (default: all).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_replay_parser()
    args = parser.parse_args(argv)

    try:
        session = replay(args.snapshot, labels=args.labels)
    except FileNotFoundError:
        print(f"error: snapshot file not found: {args.snapshot}", file=sys.stderr)
        sys.exit(1)

    if args.output_format == "json":
        import json
        data = [
            {
                "label": r.label,
                "snapshot": r.source_snapshot,
                "total": r.total,
                "success_count": r.success_count,
                "mean": r.mean,
                "median": r.median,
                "stdev": r.stdev,
            }
            for r in session.results
        ]
        print(json.dumps(data, indent=2))
    else:
        print(format_replay(session))


if __name__ == "__main__":  # pragma: no cover
    main()
