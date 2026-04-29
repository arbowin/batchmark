"""Zip multiple BatchResult sequences into paired comparison rows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import BatchResult
from batchmark.stats import mean, stdev


@dataclass
class ZippedPair:
    label: str
    left_mean: float
    right_mean: float
    left_stdev: float
    right_stdev: float
    left_success: int
    right_success: int
    left_total: int
    right_total: int

    @property
    def delta(self) -> float:
        """Absolute difference: right_mean - left_mean."""
        return self.right_mean - self.left_mean

    @property
    def ratio(self) -> Optional[float]:
        """right_mean / left_mean, or None if left_mean is zero."""
        if self.left_mean == 0.0:
            return None
        return self.right_mean / self.left_mean


@dataclass
class ZipResult:
    pairs: List[ZippedPair] = field(default_factory=list)
    left_only: List[str] = field(default_factory=list)
    right_only: List[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.pairs)


def _batch_mean(batch: BatchResult) -> float:
    times = [r.elapsed for r in batch.runs]
    return mean(times) if times else 0.0


def _batch_stdev(batch: BatchResult) -> float:
    times = [r.elapsed for r in batch.runs]
    return stdev(times) if len(times) > 1 else 0.0


def zip_batches(
    left: List[BatchResult],
    right: List[BatchResult],
) -> ZipResult:
    """Pair left and right batches by label, reporting unmatched labels."""
    left_map = {b.label: b for b in left}
    right_map = {b.label: b for b in right}

    common = set(left_map) & set(right_map)
    pairs = []
    for label in sorted(common):
        lb = left_map[label]
        rb = right_map[label]
        pairs.append(
            ZippedPair(
                label=label,
                left_mean=_batch_mean(lb),
                right_mean=_batch_mean(rb),
                left_stdev=_batch_stdev(lb),
                right_stdev=_batch_stdev(rb),
                left_success=sum(1 for r in lb.runs if r.returncode == 0),
                right_success=sum(1 for r in rb.runs if r.returncode == 0),
                left_total=len(lb.runs),
                right_total=len(rb.runs),
            )
        )

    return ZipResult(
        pairs=pairs,
        left_only=sorted(set(left_map) - set(right_map)),
        right_only=sorted(set(right_map) - set(left_map)),
    )


def format_zip(result: ZipResult, left_name: str = "left", right_name: str = "right") -> str:
    if not result.pairs:
        return "No common labels to compare."
    lines = [f"{'Label':<30} {left_name:>10} {right_name:>10} {'delta':>10} {'ratio':>8}"]
    lines.append("-" * 72)
    for p in result.pairs:
        ratio_str = f"{p.ratio:.3f}" if p.ratio is not None else "N/A"
        lines.append(
            f"{p.label:<30} {p.left_mean:>10.4f} {p.right_mean:>10.4f}"
            f" {p.delta:>+10.4f} {ratio_str:>8}"
        )
    if result.left_only:
        lines.append(f"\nOnly in {left_name}: " + ", ".join(result.left_only))
    if result.right_only:
        lines.append(f"Only in {right_name}: " + ", ".join(result.right_only))
    return "\n".join(lines)
