"""Regression detector: compares current batch results against a baseline
and classifies each label as regressed, improved, or stable."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from batchmark.runner import BatchResult
from batchmark.stats import mean


@dataclass
class RegressionEntry:
    label: str
    baseline_mean: float
    current_mean: float
    delta: float          # current - baseline
    delta_pct: float      # (delta / baseline) * 100
    verdict: str          # "regressed" | "improved" | "stable"


@dataclass
class RegressionReport:
    entries: List[RegressionEntry] = field(default_factory=list)

    def regressions(self) -> List[RegressionEntry]:
        return [e for e in self.entries if e.verdict == "regressed"]

    def improvements(self) -> List[RegressionEntry]:
        return [e for e in self.entries if e.verdict == "improved"]

    def stable(self) -> List[RegressionEntry]:
        return [e for e in self.entries if e.verdict == "stable"]


def _verdict(delta_pct: float, threshold_pct: float) -> str:
    if delta_pct > threshold_pct:
        return "regressed"
    if delta_pct < -threshold_pct:
        return "improved"
    return "stable"


def detect_regressions(
    baseline: Dict[str, float],
    current: List[BatchResult],
    threshold_pct: float = 5.0,
) -> RegressionReport:
    """Compare *current* BatchResults against *baseline* mean-time mapping.

    Args:
        baseline: mapping of label -> mean elapsed time (seconds).
        current:  list of BatchResult objects from the latest run.
        threshold_pct: percentage change required to flag as regression/improvement.

    Returns:
        RegressionReport containing one entry per label found in both sources.
    """
    if threshold_pct < 0:
        raise ValueError("threshold_pct must be >= 0")

    current_map: Dict[str, float] = {}
    for batch in current:
        if batch.times():
            current_map[batch.label] = mean(batch.times())

    entries: List[RegressionEntry] = []
    for label, base_mean in baseline.items():
        if label not in current_map:
            continue
        cur_mean = current_map[label]
        delta = cur_mean - base_mean
        delta_pct = (delta / base_mean * 100) if base_mean != 0 else 0.0
        entries.append(
            RegressionEntry(
                label=label,
                baseline_mean=base_mean,
                current_mean=cur_mean,
                delta=delta,
                delta_pct=delta_pct,
                verdict=_verdict(delta_pct, threshold_pct),
            )
        )

    return RegressionReport(entries=entries)


def format_regression_report(report: RegressionReport) -> str:
    """Return a human-readable table of regression entries."""
    if not report.entries:
        return "No common labels found between baseline and current results."

    lines = [
        f"{'Label':<30} {'Baseline':>10} {'Current':>10} {'Delta%':>8} {'Verdict'}",
        "-" * 68,
    ]
    for e in sorted(report.entries, key=lambda x: x.label):
        lines.append(
            f"{e.label:<30} {e.baseline_mean:>10.4f} {e.current_mean:>10.4f}"
            f" {e.delta_pct:>7.2f}%  {e.verdict}"
        )
    return "\n".join(lines)
