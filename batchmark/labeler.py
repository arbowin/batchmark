"""Automatic labeling of batch results based on pattern rules."""
from dataclasses import dataclass, field
from typing import List, Optional
import re
from batchmark.runner import BatchResult


@dataclass
class LabelRule:
    pattern: str
    label: str
    flags: int = 0


@dataclass
class LabeledBatch:
    batch: BatchResult
    auto_label: Optional[str]


def _match_rule(command: str, rules: List[LabelRule]) -> Optional[str]:
    for rule in rules:
        if re.search(rule.pattern, command, rule.flags):
            return rule.label
    return None


def apply_rules(batches: List[BatchResult], rules: List[LabelRule]) -> List[LabeledBatch]:
    """Apply label rules to a list of BatchResults."""
    result = []
    for batch in batches:
        auto_label = _match_rule(batch.label, rules)
        result.append(LabeledBatch(batch=batch, auto_label=auto_label))
    return result


def group_by_auto_label(labeled: List[LabeledBatch]) -> dict:
    """Group LabeledBatch entries by their auto_label value."""
    groups: dict = {}
    for item in labeled:
        key = item.auto_label or "__unlabeled__"
        groups.setdefault(key, []).append(item)
    return groups


def format_labeled(labeled: List[LabeledBatch]) -> str:
    lines = []
    for item in labeled:
        tag = item.auto_label or "(none)"
        lines.append(f"{item.batch.label} -> {tag}")
    return "\n".join(lines)
