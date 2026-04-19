"""Compute trends from benchmark history entries."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.history import History, HistoryEntry


@dataclass
class TrendPoint:
    timestamp: str
    mean: float
    success_rate: float


@dataclass
class Trend:
    label: str
    points: List[TrendPoint]
    direction: str  # "improving", "degrading", "stable"


def _success_rate(entry: HistoryEntry) -> float:
    if entry.total == 0:
        return 0.0
    return entry.success_count / entry.total


def _direction(points: List[TrendPoint]) -> str:
    if len(points) < 2:
        return "stable"
    delta = points[-1].mean - points[0].mean
    threshold = points[0].mean * 0.05  # 5% change threshold
    if delta < -threshold:
        return "improving"
    if delta > threshold:
        return "degrading"
    return "stable"


def compute_trend(label: str, history: History) -> Optional[Trend]:
    entries = [e for e in history.entries if e.label == label]
    if not entries:
        return None
    points = [
        TrendPoint(timestamp=e.timestamp, mean=e.mean, success_rate=_success_rate(e))
        for e in entries
    ]
    return Trend(label=label, points=points, direction=_direction(points))


def format_trend(trend: Trend) -> str:
    lines = [f"Trend for '{trend.label}': {trend.direction}"]
    lines.append(f"  {'Timestamp':<30} {'Mean':>10} {'Success%':>10}")
    for p in trend.points:
        lines.append(f"  {p.timestamp:<30} {p.mean:>10.4f} {p.success_rate * 100:>9.1f}%")
    return "\n".join(lines)
