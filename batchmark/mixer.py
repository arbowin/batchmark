"""mixer.py — interleave and blend runs from multiple BatchResults into new batches."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import random

from batchmark.runner import BatchResult, RunResult


@dataclass
class MixedBatch:
    label: str
    runs: List[RunResult]
    sources: List[str]

    @property
    def total(self) -> int:
        return len(self.runs)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.returncode == 0)


@dataclass
class MixResult:
    batches: List[MixedBatch]

    @property
    def count(self) -> int:
        return len(self.batches)

    def get(self, label: str) -> Optional[MixedBatch]:
        for b in self.batches:
            if b.label == label:
                return b
        return None


def _collect_by_label(
    sources: Dict[str, List[BatchResult]]
) -> Dict[str, List[tuple[str, RunResult]]]:
    """Collect (source_name, run) pairs grouped by label."""
    by_label: Dict[str, List[tuple[str, RunResult]]] = {}
    for source_name, batches in sources.items():
        for batch in batches:
            by_label.setdefault(batch.label, []).extend(
                (source_name, r) for r in batch.runs
            )
    return by_label


def mix(
    sources: Dict[str, List[BatchResult]],
    *,
    ratio: Optional[float] = None,
    seed: Optional[int] = None,
    labels: Optional[List[str]] = None,
) -> MixResult:
    """Mix runs from multiple sources into combined batches per label.

    Args:
        sources: mapping of source name -> list of BatchResults.
        ratio: fraction of runs to keep per label (0.0–1.0); None keeps all.
        seed: random seed for reproducible sampling.
        labels: restrict output to these labels; None includes all.
    """
    if not sources:
        raise ValueError("mix requires at least one source")
    if ratio is not None and not (0.0 < ratio <= 1.0):
        raise ValueError("ratio must be in (0.0, 1.0]")

    rng = random.Random(seed)
    by_label = _collect_by_label(sources)

    mixed: List[MixedBatch] = []
    target_labels = labels if labels is not None else sorted(by_label)
    for lbl in target_labels:
        pairs = by_label.get(lbl, [])
        if ratio is not None:
            k = max(1, int(len(pairs) * ratio))
            pairs = rng.sample(pairs, min(k, len(pairs)))
        seen_sources = list(dict.fromkeys(s for s, _ in pairs))
        mixed.append(MixedBatch(
            label=lbl,
            runs=[r for _, r in pairs],
            sources=seen_sources,
        ))
    return MixResult(batches=mixed)


def format_mix_summary(result: MixResult, *, precision: int = 3) -> str:
    lines = ["Mix Summary", "-" * 40]
    for mb in result.batches:
        src = ", ".join(mb.sources)
        rate = mb.success_count / mb.total if mb.total else 0.0
        lines.append(
            f"{mb.label}: {mb.total} runs, "
            f"{rate*100:.1f}% ok, sources=[{src}]"
        )
    return "\n".join(lines)
