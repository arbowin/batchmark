"""Persist and load benchmark run history to/from a JSON file."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from batchmark.runner import BatchResult
from batchmark.stats import summarize


@dataclass
class HistoryEntry:
    label: str
    timestamp: str
    mean: float
    median: float
    stdev: float
    success_count: int
    total: int


@dataclass
class History:
    entries: List[HistoryEntry] = field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def entry_from_batch(batch: BatchResult, timestamp: Optional[str] = None) -> HistoryEntry:
    s = summarize(batch)
    return HistoryEntry(
        label=batch.label,
        timestamp=timestamp or _now_iso(),
        mean=s["mean"],
        median=s["median"],
        stdev=s["stdev"],
        success_count=batch.success_count,
        total=len(batch.times),
    )


def load_history(path: str) -> History:
    if not os.path.exists(path):
        return History()
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    entries = [HistoryEntry(**e) for e in raw.get("entries", [])]
    return History(entries=entries)


def save_history(history: History, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"entries": [asdict(e) for e in history.entries]}, fh, indent=2)


def append_batch(batch: BatchResult, path: str) -> HistoryEntry:
    history = load_history(path)
    entry = entry_from_batch(batch)
    history.entries.append(entry)
    save_history(history, path)
    return entry
