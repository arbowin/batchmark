"""CLI entry point for diffing two snapshots."""
import argparse
import sys
from batchmark.snapshot import load_snapshot
from batchmark.differ import diff_batches, format_diff


def build_diff_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='batchmark-diff',
        description='Diff two batchmark snapshots and report regressions/improvements.',
    )
    p.add_argument('before', help='Path to the baseline snapshot JSON')
    p.add_argument('after', help='Path to the comparison snapshot JSON')
    p.add_argument('--threshold', type=float, default=0.02,
                   help='Percent change threshold to flag (default: 0.02)')
    p.add_argument('--regressions-only', action='store_true',
                   help='Show only regressions')
    return p


def main(argv=None):
    parser = build_diff_parser()
    args = parser.parse_args(argv)

    try:
        snap_before = load_snapshot(args.before)
        snap_after = load_snapshot(args.after)
    except FileNotFoundError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

    result = diff_batches(snap_before.batches, snap_after.batches, threshold=args.threshold)

    if args.regressions_only:
        from batchmark.differ import DiffResult
        result = DiffResult(entries=result.regressions())

    if not result.entries:
        print('No common labels to compare.')
        return

    print(f'Comparing: {snap_before.name}  →  {snap_after.name}\n')
    print(format_diff(result))
    regs = result.regressions()
    if regs:
        print(f'\n{len(regs)} regression(s) detected.')
        sys.exit(2)


if __name__ == '__main__':
    main()
