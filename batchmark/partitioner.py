"""Partition BatchResults into time-based or size-based buckets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict
import math

from batchmark.runner import BatchResult
from batchmark.stats import mean


@dataclass
class Partition:
    index: int
    batches: List[BatchResult] = field(default_factory=list)

    def run_count(self) -> int:
        return sum(len(b.times) for b in self.batches)

    def mean(self) -> float:
        times = [t for b in self.batches for t in b.times]
        return mean(times) if times else 0.0

    def labels(self) -> List[str]:
        return [b.label for b in self.batches]


@dataclass
class PartitionResult:
    strategy: str
    partitions: List[Partition]

    def count(self) -> int:
        return len(self.partitions)

    def get(self, index: int) -> Partition:
        if index < 0 or index >= len(self.partitions):
            raise IndexError(f"Partition index {index} out of range")
        return self.partitions[index]


def partition_by_size(batches: List[BatchResult], size: int) -> PartitionResult:
    """Split batches into groups of at most `size` batches each."""
    if size <= 0:
        raise ValueError("Partition size must be positive")
    if not batches:
        return PartitionResult(strategy="size", partitions=[])
    parts: List[Partition] = []
    for i in range(0, len(batches), size):
        chunk = batches[i : i + size]
        parts.append(Partition(index=len(parts), batches=chunk))
    return PartitionResult(strategy="size", partitions=parts)


def partition_by_count(batches: List[BatchResult], n: int) -> PartitionResult:
    """Split batches into exactly `n` roughly equal partitions."""
    if n <= 0:
        raise ValueError("Partition count must be positive")
    if not batches:
        return PartitionResult(strategy="count", partitions=[])
    size = math.ceil(len(batches) / n)
    parts: List[Partition] = []
    for i in range(0, len(batches), size):
        chunk = batches[i : i + size]
        parts.append(Partition(index=len(parts), batches=chunk))
    return PartitionResult(strategy="count", partitions=parts)


def format_partition_result(result: PartitionResult) -> str:
    lines = [f"Partitions ({result.strategy}): {result.count()} total"]
    for p in result.partitions:
        lines.append(
            f"  [{p.index}] batches={len(p.batches)} runs={p.run_count()} mean={p.mean():.4f}s labels={p.labels()}"
        )
    return "\n".join(lines)
