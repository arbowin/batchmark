"""Bucketer: groups BatchResult runs into time-based or count-based buckets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from batchmark.runner import BatchResult, RunResult
from batchmark.stats import mean, summarize


@dataclass
class Bucket:
    index: int
    label: str
    runs: List[RunResult] = field(default_factory=list)

    def run_count(self) -> int:
        return len(self.runs)

    def mean(self) -> float:
        times = [r.elapsed for r in self.runs if r.success]
        return mean(times) if times else 0.0

    def success_rate(self) -> float:
        if not self.runs:
            return 0.0
        return sum(1 for r in self.runs if r.success) / len(self.runs)


@dataclass
class BucketResult:
    label: str
    bucket_size: int
    buckets: List[Bucket]

    def bucket_count(self) -> int:
        return len(self.buckets)

    def best_bucket(self) -> Bucket | None:
        filled = [b for b in self.buckets if b.runs]
        return min(filled, key=lambda b: b.mean()) if filled else None

    def worst_bucket(self) -> Bucket | None:
        filled = [b for b in self.buckets if b.runs]
        return max(filled, key=lambda b: b.mean()) if filled else None


def bucket_batch(batch: BatchResult, bucket_size: int) -> BucketResult:
    """Split a BatchResult's runs into sequential buckets of `bucket_size`."""
    if bucket_size < 1:
        raise ValueError("bucket_size must be >= 1")
    runs = batch.runs
    buckets: List[Bucket] = []
    for i in range(0, max(len(runs), 1), bucket_size):
        chunk = runs[i : i + bucket_size]
        buckets.append(Bucket(index=len(buckets), label=batch.label, runs=chunk))
    return BucketResult(label=batch.label, bucket_size=bucket_size, buckets=buckets)


def bucket_all(batches: List[BatchResult], bucket_size: int) -> Dict[str, BucketResult]:
    """Apply bucket_batch to every BatchResult, keyed by label."""
    return {b.label: bucket_batch(b, bucket_size) for b in batches}


def format_bucket_result(result: BucketResult) -> str:
    lines = [f"Buckets for '{result.label}' (size={result.bucket_size})"]
    lines.append(f"  Total buckets : {result.bucket_count()}")
    for b in result.buckets:
        lines.append(
            f"  Bucket {b.index:>3}: runs={b.run_count():>4}  "
            f"mean={b.mean():.4f}s  success={b.success_rate():.1%}"
        )
    return "\n".join(lines)
