import math
from typing import List


def mean(values: List[float]) -> float:
    if not values:
        raise ValueError("Cannot compute mean of empty list")
    return sum(values) / len(values)


def median(values: List[float]) -> float:
    if not values:
        raise ValueError("Cannot compute median of empty list")
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]


def stdev(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    variance = sum((v - m) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def summarize(values: List[float]) -> dict:
    """Return a statistical summary dict for a list of floats."""
    return {
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
        "median": median(values),
        "stdev": stdev(values),
        "count": len(values),
    }
