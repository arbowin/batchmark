"""Normalize benchmark timing results to a common baseline for cross-run comparison."""

from dataclasses import dataclass, field
from typing import List, Optional
from batchmark.runner import BatchResult
from batchmark.stats import mean


@dataclass
class NormalizedEntry:
    label: str
    raw_mean: float
    baseline_mean: float
    normalized_score: float  # raw_mean / baseline_mean; <1.0 is faster
    speedup: float           # baseline_mean / raw_mean; >1.0 is faster


@dataclass
class NormalizationResult:
    baseline_label: str
    entries: List[NormalizedEntry] = field(default_factory=list)

    def fastest(self) -> Optional[NormalizedEntry]:
        if not self.entries:
            return None
        return min(self.entries, key=lambda e: e.normalized_score)

    def slowest(self) -> Optional[NormalizedEntry]:
        if not self.entries:
            return None
        return max(self.entries, key=lambda e: e.normalized_score)


def _batch_mean(batch: BatchResult) -> float:
    times = [r.elapsed for r in batch.runs if r.success]
    if not times:
        return float("inf")
    return mean(times)


def normalize(batches: List[BatchResult], baseline_label: str) -> NormalizationResult:
    """Normalize all batch results relative to the batch with baseline_label."""
    if not batches:
        raise ValueError("No batches provided for normalization.")

    baseline_batch = next((b for b in batches if b.label == baseline_label), None)
    if baseline_batch is None:
        raise ValueError(f"Baseline label '{baseline_label}' not found in batches.")

    baseline_mean_val = _batch_mean(baseline_batch)
    if baseline_mean_val == 0.0 or baseline_mean_val == float("inf"):
        raise ValueError("Baseline mean is zero or undefined; cannot normalize.")

    entries: List[NormalizedEntry] = []
    for batch in batches:
        raw = _batch_mean(batch)
        normalized = raw / baseline_mean_val
        speedup = baseline_mean_val / raw if raw > 0 else float("inf")
        entries.append(NormalizedEntry(
            label=batch.label,
            raw_mean=raw,
            baseline_mean=baseline_mean_val,
            normalized_score=normalized,
            speedup=speedup,
        ))

    entries.sort(key=lambda e: e.normalized_score)
    return NormalizationResult(baseline_label=baseline_label, entries=entries)


def format_normalization(result: NormalizationResult) -> str:
    """Return a human-readable table of normalized scores."""
    lines = [
        f"Normalization (baseline: {result.baseline_label})",
        f"{'Label':<30} {'Raw Mean':>12} {'Normalized':>12} {'Speedup':>10}",
        "-" * 68,
    ]
    for e in result.entries:
        marker = " *" if e.label == result.baseline_label else ""
        lines.append(
            f"{e.label:<30} {e.raw_mean:>12.4f} {e.normalized_score:>12.4f} {e.speedup:>10.4f}{marker}"
        )
    return "\n".join(lines)
