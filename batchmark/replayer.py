"""Replay saved snapshots and re-run statistical analysis without executing commands."""

from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import BatchResult, RunResult
from batchmark.snapshot import load_snapshot, Snapshot
from batchmark.stats import summarize


@dataclass
class ReplayResult:
    label: str
    source_snapshot: str
    runs: List[RunResult]
    mean: float
    median: float
    stdev: float
    success_count: int
    total: int

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.success_count / self.total


@dataclass
class ReplaySession:
    snapshot_name: str
    results: List[ReplayResult] = field(default_factory=list)


def _replay_batch(batch: BatchResult, snapshot_name: str) -> ReplayResult:
    """Compute statistics from an existing BatchResult without re-running."""
    times = [r.elapsed for r in batch.runs]
    stats = summarize(times) if times else {"mean": 0.0, "median": 0.0, "stdev": 0.0}
    successes = sum(1 for r in batch.runs if r.success)
    return ReplayResult(
        label=batch.label,
        source_snapshot=snapshot_name,
        runs=list(batch.runs),
        mean=stats["mean"],
        median=stats["median"],
        stdev=stats["stdev"],
        success_count=successes,
        total=len(batch.runs),
    )


def replay(snapshot_path: str, labels: Optional[List[str]] = None) -> ReplaySession:
    """Load a snapshot and replay analysis for all (or selected) labels."""
    snap: Snapshot = load_snapshot(snapshot_path)
    selected = [
        b for b in snap.batches
        if labels is None or b.label in labels
    ]
    results = [_replay_batch(b, snap.name) for b in selected]
    return ReplaySession(snapshot_name=snap.name, results=results)


def format_replay(session: ReplaySession) -> str:
    """Return a human-readable summary of a replay session."""
    lines = [f"Replay: {session.snapshot_name}", ""]
    for r in session.results:
        lines.append(f"  [{r.label}]")
        lines.append(f"    runs   : {r.total}")
        lines.append(f"    success: {r.success_count}/{r.total} ({r.success_rate:.0%})")
        lines.append(f"    mean   : {r.mean:.4f}s")
        lines.append(f"    median : {r.median:.4f}s")
        lines.append(f"    stdev  : {r.stdev:.4f}s")
        lines.append("")
    return "\n".join(lines)
