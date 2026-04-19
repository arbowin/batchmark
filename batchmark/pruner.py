"""Pruner: remove old or low-quality entries from history."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from batchmark.history import HistoryEntry


@dataclass
class PruneResult:
    kept: List[HistoryEntry]
    removed: List[HistoryEntry]


def _success_rate(entry: HistoryEntry) -> float:
    if entry.total == 0:
        return 0.0
    return entry.successes / entry.total


def prune_by_age(entries: List[HistoryEntry], keep_last: int) -> PruneResult:
    """Keep only the most recent `keep_last` entries per label."""
    from collections import defaultdict
    by_label: dict = defaultdict(list)
    for e in entries:
        by_label[e.label].append(e)
    kept, removed = [], []
    for label, group in by_label.items():
        sorted_group = sorted(group, key=lambda e: e.timestamp, reverse=True)
        kept.extend(sorted_group[:keep_last])
        removed.extend(sorted_group[keep_last:])
    return PruneResult(kept=kept, removed=removed)


def prune_by_success_rate(entries: List[HistoryEntry], min_rate: float) -> PruneResult:
    """Remove entries whose success rate is below min_rate."""
    kept = [e for e in entries if _success_rate(e) >= min_rate]
    removed = [e for e in entries if _success_rate(e) < min_rate]
    return PruneResult(kept=kept, removed=removed)


def prune(entries: List[HistoryEntry], keep_last: int = 50, min_success_rate: float = 0.0) -> PruneResult:
    """Apply both age and success-rate pruning."""
    r1 = prune_by_age(entries, keep_last)
    r2 = prune_by_success_rate(r1.kept, min_success_rate)
    return PruneResult(kept=r2.kept, removed=r1.removed + r2.removed)


def format_prune_result(result: PruneResult) -> str:
    lines = [
        f"Kept   : {len(result.kept)} entries",
        f"Removed: {len(result.removed)} entries",
    ]
    return "\n".join(lines)
