"""Score batch results using a weighted formula for ranking."""
from dataclasses import dataclass
from typing import List
from batchmark.runner import BatchResult
from batchmark.stats import summarize
from batchmark.filter import success_rate


@dataclass
class ScoredResult:
    label: str
    mean: float
    success_rate: float
    score: float


def score(
    result: BatchResult,
    time_weight: float = 0.7,
    success_weight: float = 0.3,
    baseline_mean: float = 1.0,
) -> ScoredResult:
    """Compute a composite score for a batch result.

    Lower score is better. Score combines normalized mean time and
    inverted success rate.
    """
    if time_weight + success_weight == 0:
        raise ValueError("Weights must not both be zero")

    s = summarize(result)
    sr = success_rate(result)

    normalized_time = s.mean / baseline_mean if baseline_mean > 0 else s.mean
    failure_rate = 1.0 - sr

    composite = time_weight * normalized_time + success_weight * failure_rate

    return ScoredResult(
        label=result.label,
        mean=s.mean,
        success_rate=sr,
        score=round(composite, 6),
    )


def score_all(
    results: List[BatchResult],
    time_weight: float = 0.7,
    success_weight: float = 0.3,
) -> List[ScoredResult]:
    """Score and rank a list of batch results. Lower score = better."""
    if not results:
        return []

    means = [summarize(r).mean for r in results]
    baseline = max(means) if means else 1.0

    scored = [
        score(r, time_weight=time_weight, success_weight=success_weight, baseline_mean=baseline)
        for r in results
    ]
    return sorted(scored, key=lambda s: s.score)


def format_scores(scored: List[ScoredResult]) -> str:
    """Return a human-readable table of scored results."""
    if not scored:
        return "No results to score."
    lines = [f"{'Rank':<6}{'Label':<30}{'Mean':>10}{'Success%':>10}{'Score':>10}"]
    lines.append("-" * 66)
    for rank, s in enumerate(scored, 1):
        lines.append(
            f"{rank:<6}{s.label:<30}{s.mean:>10.4f}{s.success_rate*100:>9.1f}%{s.score:>10.4f}"
        )
    return "\n".join(lines)
