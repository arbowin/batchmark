"""Stack multiple BatchResult lists into a unified multi-source view."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from batchmark.runner import BatchResult
from batchmark.stats import mean, stdev


@dataclass
class StackedLayer:
    source: str
    label: str
    mean: float
    stdev: float
    run_count: int
    success_count: int

    @property
    def success_rate(self) -> float:
        if self.run_count == 0:
            return 0.0
        return self.success_count / self.run_count


@dataclass
class StackResult:
    sources: List[str]
    layers: List[StackedLayer] = field(default_factory=list)

    @property
    def labels(self) -> List[str]:
        seen: List[str] = []
        for layer in self.layers:
            if layer.label not in seen:
                seen.append(layer.label)
        return seen

    def by_label(self, label: str) -> List[StackedLayer]:
        return [lyr for lyr in self.layers if lyr.label == label]

    def by_source(self, source: str) -> List[StackedLayer]:
        return [lyr for lyr in self.layers if lyr.source == source]


def stack(
    sources: Dict[str, List[BatchResult]],
) -> StackResult:
    """Stack named sources of BatchResult lists into a StackResult."""
    if not sources:
        raise ValueError("sources must not be empty")

    source_names = list(sources.keys())
    result = StackResult(sources=source_names)

    for source_name, batches in sources.items():
        for batch in batches:
            times = [r.elapsed for r in batch.runs]
            sc = sum(1 for r in batch.runs if r.returncode == 0)
            layer = StackedLayer(
                source=source_name,
                label=batch.label,
                mean=mean(times) if times else 0.0,
                stdev=stdev(times) if len(times) > 1 else 0.0,
                run_count=len(times),
                success_count=sc,
            )
            result.layers.append(layer)

    return result


def format_stack(result: StackResult, precision: int = 4) -> str:
    """Format a StackResult as a human-readable table."""
    lines: List[str] = []
    header = f"{'Label':<24} {'Source':<16} {'Mean':>10} {'Stdev':>10} {'Runs':>6} {'OK%':>7}"
    lines.append(header)
    lines.append("-" * len(header))
    for label in result.labels:
        for layer in result.by_label(label):
            ok_pct = f"{layer.success_rate * 100:.1f}%"
            lines.append(
                f"{layer.label:<24} {layer.source:<16}"
                f" {layer.mean:>{precision + 6}.{precision}f}"
                f" {layer.stdev:>{precision + 6}.{precision}f}"
                f" {layer.run_count:>6} {ok_pct:>7}"
            )
    return "\n".join(lines)
