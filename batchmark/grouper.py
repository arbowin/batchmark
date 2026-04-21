"""Group BatchResults by a key function or label pattern."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from batchmark.runner import BatchResult


@dataclass
class GroupedBatches:
    """A named collection of BatchResult groups."""
    groups: Dict[str, List[BatchResult]] = field(default_factory=dict)

    def keys(self) -> List[str]:
        return list(self.groups.keys())

    def get(self, key: str) -> List[BatchResult]:
        return self.groups.get(key, [])

    def size(self) -> int:
        return len(self.groups)


def group_by_key(
    batches: List[BatchResult],
    key_fn: Callable[[BatchResult], str],
) -> GroupedBatches:
    """Group batches by the string returned by key_fn."""
    if not batches:
        raise ValueError("Cannot group an empty list of batches")
    groups: Dict[str, List[BatchResult]] = {}
    for batch in batches:
        k = key_fn(batch)
        groups.setdefault(k, []).append(batch)
    return GroupedBatches(groups=groups)


def group_by_prefix(batches: List[BatchResult], sep: str = ":") -> GroupedBatches:
    """Group batches whose labels share a common prefix before *sep*."""
    def _prefix(b: BatchResult) -> str:
        return b.label.split(sep, 1)[0] if sep in b.label else b.label

    return group_by_key(batches, _prefix)


def group_by_label(batches: List[BatchResult]) -> GroupedBatches:
    """Group batches by their exact label (identity grouping)."""
    return group_by_key(batches, lambda b: b.label)


def format_grouped(grouped: GroupedBatches) -> str:
    """Return a human-readable summary of grouped batches."""
    lines: List[str] = []
    for key, members in grouped.groups.items():
        lines.append(f"[{key}]  {len(members)} batch(es)")
        for b in members:
            lines.append(f"  - {b.label}  runs={b.total}")
    return "\n".join(lines)
