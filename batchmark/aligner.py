"""Align multiple BatchResult sets to a common set of labels.

Useful when comparing runs that may not share all labels — missing
entries are filled with a configurable placeholder so downstream
modules always receive uniform data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from batchmark.runner import BatchResult, RunResult


@dataclass
class AlignedSource:
    name: str
    batches: Dict[str, BatchResult]  # label -> BatchResult
    missing_labels: List[str] = field(default_factory=list)


@dataclass
class AlignResult:
    sources: List[AlignedSource]
    common_labels: List[str]
    all_labels: List[str]


def _all_labels(sources: List[List[BatchResult]]) -> List[str]:
    seen: Set[str] = set()
    ordered: List[str] = []
    for batches in sources:
        for b in batches:
            if b.label not in seen:
                seen.add(b.label)
                ordered.append(b.label)
    return ordered


def _common_labels(sources: List[List[BatchResult]]) -> List[str]:
    if not sources:
        return []
    sets = [set(b.label for b in src) for src in sources]
    common = sets[0].intersection(*sets[1:])
    return [lbl for lbl in _all_labels(sources) if lbl in common]


def _make_placeholder(label: str) -> BatchResult:
    """Return an empty BatchResult for *label* used as a fill-in."""
    return BatchResult(label=label, runs=[])


def align(
    sources: List[List[BatchResult]],
    names: Optional[List[str]] = None,
    fill_missing: bool = True,
) -> AlignResult:
    """Align *sources* to a shared label space.

    Parameters
    ----------
    sources:
        Each element is the list of BatchResults from one benchmark run.
    names:
        Human-readable names for each source (default: "source-0", …).
    fill_missing:
        When *True*, labels absent in a source are filled with an empty
        placeholder BatchResult.  When *False* they are simply recorded
        in *missing_labels* but not inserted.
    """
    if not sources:
        raise ValueError("align() requires at least one source")

    if names is None:
        names = [f"source-{i}" for i in range(len(sources))]

    if len(names) != len(sources):
        raise ValueError("len(names) must equal len(sources)")

    all_lbls = _all_labels(sources)
    common_lbls = _common_labels(sources)

    aligned_sources: List[AlignedSource] = []
    for name, batches in zip(names, sources):
        index: Dict[str, BatchResult] = {b.label: b for b in batches}
        missing: List[str] = [lbl for lbl in all_lbls if lbl not in index]
        if fill_missing:
            for lbl in missing:
                index[lbl] = _make_placeholder(lbl)
        aligned_sources.append(
            AlignedSource(name=name, batches=index, missing_labels=missing)
        )

    return AlignResult(
        sources=aligned_sources,
        common_labels=common_lbls,
        all_labels=all_lbls,
    )


def format_alignment(result: AlignResult) -> str:
    lines = [f"Aligned {len(result.sources)} source(s)"]
    lines.append(f"  All labels    : {', '.join(result.all_labels)}")
    lines.append(f"  Common labels : {', '.join(result.common_labels)}")
    for src in result.sources:
        missing_str = ", ".join(src.missing_labels) if src.missing_labels else "none"
        lines.append(f"  [{src.name}] missing: {missing_str}")
    return "\n".join(lines)
