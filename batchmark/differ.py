"""Diff two benchmark runs and highlight regressions or improvements."""
from dataclasses import dataclass
from typing import Optional
from batchmark.runner import BatchResult
from batchmark.stats import summarize


@dataclass
class DiffEntry:
    label: str
    mean_before: float
    mean_after: float
    delta: float          # absolute ms
    pct_change: float     # percent
    verdict: str          # 'improved', 'regressed', 'unchanged'


@dataclass
class DiffResult:
    entries: list

    def regressions(self):
        return [e for e in self.entries if e.verdict == 'regressed']

    def improvements(self):
        return [e for e in self.entries if e.verdict == 'improved']


_THRESHOLD = 0.02  # 2% change to count as meaningful


def _verdict(pct: float) -> str:
    if pct > _THRESHOLD:
        return 'regressed'
    if pct < -_THRESHOLD:
        return 'improved'
    return 'unchanged'


def diff_batches(before: list, after: list, threshold: float = _THRESHOLD) -> DiffResult:
    """Compare two lists of BatchResult by label."""
    before_map = {b.label: b for b in before}
    after_map = {a.label: a for a in after}
    common = set(before_map) & set(after_map)
    entries = []
    for label in sorted(common):
        s_before = summarize(before_map[label].times)
        s_after = summarize(after_map[label].times)
        delta = s_after['mean'] - s_before['mean']
        pct = delta / s_before['mean'] if s_before['mean'] else 0.0
        entries.append(DiffEntry(
            label=label,
            mean_before=s_before['mean'],
            mean_after=s_after['mean'],
            delta=delta,
            pct_change=pct,
            verdict=_verdict(pct),
        ))
    return DiffResult(entries=entries)


def format_diff(result: DiffResult) -> str:
    lines = [f"{'Label':<30} {'Before':>10} {'After':>10} {'Delta':>10} {'%':>8} {'Verdict':<12}"]
    lines.append('-' * 82)
    for e in result.entries:
        lines.append(
            f"{e.label:<30} {e.mean_before:>10.3f} {e.mean_after:>10.3f} "
            f"{e.delta:>+10.3f} {e.pct_change*100:>+7.1f}% {e.verdict:<12}"
        )
    return '\n'.join(lines)
