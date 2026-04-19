from dataclasses import dataclass, field
from typing import Dict, List
from batchmark.runner import BatchResult


@dataclass
class TaggedResult:
    batch: BatchResult
    tags: List[str] = field(default_factory=list)


@dataclass
class TagIndex:
    entries: List[TaggedResult] = field(default_factory=list)

    def all_tags(self) -> List[str]:
        tags = set()
        for e in self.entries:
            tags.update(e.tags)
        return sorted(tags)

    def by_tag(self, tag: str) -> List[TaggedResult]:
        return [e for e in self.entries if tag in e.tags]

    def by_label(self, label: str) -> List[TaggedResult]:
        return [e for e in self.entries if e.batch.label == label]


def tag_result(batch: BatchResult, tags: List[str]) -> TaggedResult:
    normalized = [t.strip().lower() for t in tags if t.strip()]
    return TaggedResult(batch=batch, tags=normalized)


def build_index(tagged: List[TaggedResult]) -> TagIndex:
    return TagIndex(entries=list(tagged))


def filter_by_tags(index: TagIndex, tags: List[str]) -> List[TaggedResult]:
    """Return entries that have ALL of the given tags."""
    required = {t.strip().lower() for t in tags}
    return [e for e in index.entries if required.issubset(set(e.tags))]


def format_tagged(tagged: TaggedResult) -> str:
    tags_str = ", ".join(tagged.tags) if tagged.tags else "(none)"
    return f"[{tagged.batch.label}] tags: {tags_str}"
