"""Annotator: attach free-form notes to BatchResults."""
from dataclasses import dataclass, field
from typing import Dict, List
from batchmark.runner import BatchResult


@dataclass
class AnnotatedResult:
    batch: BatchResult
    notes: List[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return self.batch.label


@dataclass
class AnnotationIndex:
    entries: List[AnnotatedResult] = field(default_factory=list)


def annotate(batch: BatchResult, notes: List[str]) -> AnnotatedResult:
    """Attach notes to a BatchResult."""
    cleaned = [n.strip() for n in notes if n.strip()]
    return AnnotatedResult(batch=batch, notes=cleaned)


def build_index(results: List[AnnotatedResult]) -> AnnotationIndex:
    """Build a searchable index of annotated results."""
    return AnnotationIndex(entries=list(results))


def by_note_keyword(index: AnnotationIndex, keyword: str) -> List[AnnotatedResult]:
    """Return entries whose notes contain the given keyword (case-insensitive)."""
    kw = keyword.lower()
    return [e for e in index.entries if any(kw in n.lower() for n in e.notes)]


def format_annotated(result: AnnotatedResult) -> str:
    """Return a human-readable string for an annotated result."""
    lines = [f"[{result.label}]"]
    if result.notes:
        for note in result.notes:
            lines.append(f"  note: {note}")
    else:
        lines.append("  (no notes)")
    return "\n".join(lines)
