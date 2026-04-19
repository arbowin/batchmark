"""Statistical helpers for benchmark results."""

import math
from typing import List


def mean(times: List[float]) -> float:
    if not times:
        return 0.0
    return sum(times) / len(times)


def median(times: List[float]) -> float:
    if not times:
        return 0.0
    s = sorted(times)
    n = len(s)
    mid = n // 2
    if n % 2 == 0:
        return (s[mid - 1] + s[mid]) / 2
    return s[mid]


def stdev(times: List[float]) -> float:
    if len(times) < 2:
        return 0.0
    m = mean(times)
    variance = sum((t - m) ** 2 for t in times) / (len(times) - 1)
    return math.sqrt(variance)


def summarize(batch_result) -> dict:
    """Return a dict of stats for a BatchResult."""
    t = batch_result.times
    return {
        "mean": round(mean(t), 6),
        "median": round(median(t), 6),
        "stdev": round(stdev(t), 6),
        "min": round(min(t), 6) if t else 0.0,
        "max": round(max(t), 6) if t else 0.0,
    }
