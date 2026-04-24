"""Split a list of BatchResults into train/test or ratio-based subsets."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Sequence

from batchmark.runner import BatchResult


@dataclass
class SplitResult:
    label: str
    train: List[BatchResult] = field(default_factory=list)
    test: List[BatchResult] = field(default_factory=list)

    @property
    def train_count(self) -> int:
        return len(self.train)

    @property
    def test_count(self) -> int:
        return len(self.test)

    @property
    def total(self) -> int:
        return self.train_count + self.test_count


def _validate_ratio(ratio: float) -> None:
    if not (0.0 < ratio < 1.0):
        raise ValueError(f"ratio must be between 0 and 1 exclusive, got {ratio}")


def split_batch(batch: BatchResult, ratio: float = 0.8, shuffle: bool = False) -> SplitResult:
    """Split a single BatchResult's runs into train/test by ratio."""
    _validate_ratio(ratio)
    runs = list(batch.runs)
    if shuffle:
        import random
        random.shuffle(runs)
    cut = max(1, math.floor(len(runs) * ratio)) if runs else 0
    from batchmark.runner import BatchResult as BR
    train_batch = BR(label=batch.label, runs=runs[:cut])
    test_batch = BR(label=batch.label, runs=runs[cut:])
    return SplitResult(label=batch.label, train=[train_batch], test=[test_batch])


def split_all(
    batches: Sequence[BatchResult],
    ratio: float = 0.8,
    shuffle: bool = False,
) -> List[SplitResult]:
    """Split every BatchResult in the sequence and return one SplitResult per batch."""
    if not batches:
        raise ValueError("batches must not be empty")
    return [split_batch(b, ratio=ratio, shuffle=shuffle) for b in batches]


def format_split(result: SplitResult) -> str:
    lines = [
        f"Split: {result.label}",
        f"  train : {result.train_count} batch(es), "
        f"{sum(b.run_count for b in result.train)} run(s)",
        f"  test  : {result.test_count} batch(es), "
        f"{sum(b.run_count for b in result.test)} run(s)",
        f"  total : {result.total} batch(es)",
    ]
    return "\n".join(lines)
