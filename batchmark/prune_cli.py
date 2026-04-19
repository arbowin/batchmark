"""CLI entry point for pruning history files."""
from __future__ import annotations
import argparse
import json
import sys
from batchmark.history import HistoryEntry, load_history, save_history
from batchmark.pruner import prune, format_prune_result


def build_prune_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-prune",
        description="Prune old or low-quality entries from a history file.",
    )
    parser.add_argument("history_file", help="Path to the JSON history file.")
    parser.add_argument(
        "--keep-last",
        type=int,
        default=50,
        dest="keep_last",
        help="Maximum number of recent entries to keep per label (default: 50).",
    )
    parser.add_argument(
        "--min-success-rate",
        type=float,
        default=0.0,
        dest="min_success_rate",
        help="Minimum success rate threshold (0.0-1.0, default: 0.0).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be removed without modifying the file.",
    )
    return parser


def main(argv=None) -> None:
    parser = build_prune_parser()
    args = parser.parse_args(argv)

    try:
        history = load_history(args.history_file)
    except FileNotFoundError:
        print(f"Error: history file not found: {args.history_file}", file=sys.stderr)
        sys.exit(1)

    result = prune(
        history.entries,
        keep_last=args.keep_last,
        min_success_rate=args.min_success_rate,
    )

    print(format_prune_result(result))

    if args.dry_run:
        print("Dry run — no changes written.")
        return

    history.entries = result.kept
    save_history(history, args.history_file)
    print(f"History saved to {args.history_file}.")


if __name__ == "__main__":
    main()
