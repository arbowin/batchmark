import argparse
import sys
from batchmark.runner import benchmark_command
from batchmark.ranker import rank, format_ranking


def build_rank_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-rank",
        description="Rank multiple shell commands by performance",
    )
    parser.add_argument(
        "commands",
        nargs="+",
        metavar="CMD",
        help="Shell commands to benchmark and rank",
    )
    parser.add_argument(
        "-n", "--iterations",
        type=int,
        default=5,
        help="Number of iterations per command (default: 5)",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        metavar="LABEL",
        help="Optional labels for each command (must match command count)",
    )
    return parser


def main(argv=None):
    parser = build_rank_parser()
    args = parser.parse_args(argv)

    labels = args.labels
    if labels and len(labels) != len(args.commands):
        print("Error: number of labels must match number of commands", file=sys.stderr)
        sys.exit(1)

    batches = []
    for i, cmd in enumerate(args.commands):
        label = labels[i] if labels else cmd
        try:
            result = benchmark_command(cmd, iterations=args.iterations, label=label)
            batches.append(result)
        except Exception as e:
            print(f"Error benchmarking '{cmd}': {e}", file=sys.stderr)
            sys.exit(1)

    ranking = rank(batches)
    print(format_ranking(ranking))


if __name__ == "__main__":
    main()
