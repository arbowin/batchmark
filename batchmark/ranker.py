from dataclasses import dataclass, field
from typing import List, Optional
from batchmark.runner import BatchResult
from batchmark.stats import summarize


@dataclass
class RankedResult:
    rank: int
    label: str
    mean: float
    success_rate: float
    score: float


@dataclass
class RankingResult:
    entries: List[RankedResult] = field(default_factory=list)

    def best(self) -> Optional[RankedResult]:
        return self.entries[0] if self.entries else None

    def worst(self) -> Optional[RankedResult]:
        return self.entries[-1] if self.entries else None


def _success_rate(batch: BatchResult) -> float:
    if batch.total == 0:
        return 0.0
    return batch.successes / batch.total


def _composite_score(mean: float, success_rate: float) -> float:
    """Lower mean is better; higher success rate is better."""
    penalty = (1.0 - success_rate) * 1000.0
    return mean + penalty


def rank(batches: List[BatchResult]) -> RankingResult:
    if not batches:
        raise ValueError("No batches to rank")

    scored = []
    for batch in batches:
        s = summarize(batch.times)
        sr = _success_rate(batch)
        score = _composite_score(s.mean, sr)
        scored.append((batch.label, s.mean, sr, score))

    scored.sort(key=lambda x: x[3])

    entries = [
        RankedResult(rank=i + 1, label=label, mean=mean, success_rate=sr, score=score)
        for i, (label, mean, sr, score) in enumerate(scored)
    ]
    return RankingResult(entries=entries)


def format_ranking(result: RankingResult) -> str:
    lines = ["Ranking:", f"  {'Rank':<6} {'Label':<24} {'Mean':>10} {'Success%':>10} {'Score':>10}"]
    lines.append("  " + "-" * 64)
    for e in result.entries:
        lines.append(
            f"  {e.rank:<6} {e.label:<24} {e.mean:>10.4f} {e.success_rate * 100:>9.1f}% {e.score:>10.4f}"
        )
    return "\n".join(lines)
