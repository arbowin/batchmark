"""Outlier detection for benchmark run results."""

from dataclasses import dataclass, field
from typing import List, Optional
from batchmark.runner import BatchResult
from batchmark.stats import mean, stdev


@dataclass
class OutlierResult:
    label: str
    times: List[float]
    outliers: List[float]
    clean: List[float]
    threshold_low: float
    threshold_high: float

    @property
    def outlier_count(self) -> int:
        return len(self.outliers)

    @property
    def has_outliers(self) -> bool:
        return len(self.outliers) > 0


def _iqr_bounds(times: List[float]) -> tuple:
    """Return (low, high) bounds using 1.5*IQR rule."""
    sorted_t = sorted(times)
    n = len(sorted_t)
    q1 = sorted_t[n // 4]
    q3 = sorted_t[(3 * n) // 4]
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def _zscore_bounds(times: List[float], z: float = 2.5) -> tuple:
    """Return (low, high) bounds using z-score threshold."""
    if len(times) < 2:
        return float("-inf"), float("inf")
    m = mean(times)
    s = stdev(times)
    if s == 0:
        return float("-inf"), float("inf")
    return m - z * s, m + z * s


def detect_outliers(
    batch: BatchResult,
    method: str = "iqr",
    z_threshold: float = 2.5,
) -> Optional[OutlierResult]:
    """Detect outliers in a BatchResult's run times.

    Args:
        batch: The BatchResult to analyse.
        method: 'iqr' or 'zscore'.
        z_threshold: Z-score cutoff (only used when method='zscore').

    Returns:
        OutlierResult or None if fewer than 4 data points.
    """
    times = [r.elapsed for r in batch.runs if r.elapsed is not None]
    if len(times) < 4:
        return None

    if method == "zscore":
        low, high = _zscore_bounds(times, z_threshold)
    else:
        low, high = _iqr_bounds(times)

    outliers = [t for t in times if t < low or t > high]
    clean = [t for t in times if low <= t <= high]

    return OutlierResult(
        label=batch.label,
        times=times,
        outliers=outliers,
        clean=clean,
        threshold_low=low,
        threshold_high=high,
    )


def format_outlier_report(result: OutlierResult) -> str:
    """Return a human-readable summary of detected outliers."""
    lines = [
        f"Outlier Report: {result.label}",
        f"  Total samples : {len(result.times)}",
        f"  Outliers found: {result.outlier_count}",
        f"  Bounds        : [{result.threshold_low:.4f}s, {result.threshold_high:.4f}s]",
    ]
    if result.has_outliers:
        formatted = ", ".join(f"{v:.4f}s" for v in sorted(result.outliers))
        lines.append(f"  Outlier values: {formatted}")
    else:
        lines.append("  No outliers detected.")
    return "\n".join(lines)
