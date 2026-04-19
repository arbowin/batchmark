"""Baseline management: save and compare against a reference BatchResult."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from batchmark.runner import BatchResult
from batchmark.stats import summarize


@dataclass
class BaselineComparison:
    label: str
    baseline_mean: float
    current_mean: float
    delta: float          # current - baseline
    delta_pct: float      # percent change
    improved: bool


def save_baseline(results: list[BatchResult], path: str | Path) -> None:
    """Persist a list of BatchResults as a baseline JSON file."""
    path = Path(path)
    data = []
    for br in results:
        s = summarize(br)
        data.append({
            "label": br.label,
            "mean": s["mean"],
            "median": s["median"],
            "stdev": s["stdev"],
            "iterations": len(br.times),
            "success_count": br.success_count,
        })
    path.write_text(json.dumps(data, indent=2))


def load_baseline(path: str | Path) -> dict[str, dict]:
    """Load baseline from JSON; returns mapping label -> stats dict."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Baseline file not found: {path}")
    raw = json.loads(path.read_text())
    return {entry["label"]: entry for entry in raw}


def compare_to_baseline(
    results: list[BatchResult],
    baseline: dict[str, dict],
) -> list[BaselineComparison]:
    """Compare current results against a loaded baseline."""
    comparisons: list[BaselineComparison] = []
    for br in results:
        if br.label not in baseline:
            continue
        base = baseline[br.label]
        s = summarize(br)
        current_mean = s["mean"]
        baseline_mean = base["mean"]
        delta = current_mean - baseline_mean
        delta_pct = (delta / baseline_mean * 100) if baseline_mean != 0 else 0.0
        comparisons.append(BaselineComparison(
            label=br.label,
            baseline_mean=baseline_mean,
            current_mean=current_mean,
            delta=delta,
            delta_pct=delta_pct,
            improved=delta < 0,
        ))
    return comparisons


def format_baseline_comparison(comparisons: list[BaselineComparison]) -> str:
    lines = ["Baseline Comparison", "-" * 40]
    for c in comparisons:
        direction = "improved" if c.improved else "regressed"
        lines.append(
            f"{c.label}: {c.baseline_mean:.4f}s -> {c.current_mean:.4f}s "
            f"({c.delta_pct:+.1f}%) [{direction}]"
        )
    return "\n".join(lines)
