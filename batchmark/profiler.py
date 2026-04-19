"""Memory and CPU profiling utilities for benchmark runs."""

from __future__ import annotations

import resource
import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProfileSample:
    elapsed: float
    peak_memory_kb: int
    cpu_user: float
    cpu_sys: float


@dataclass
class ProfileResult:
    label: str
    samples: List[ProfileSample] = field(default_factory=list)

    def avg_memory_kb(self) -> float:
        if not self.samples:
            return 0.0
        return sum(s.peak_memory_kb for s in self.samples) / len(self.samples)

    def avg_cpu_user(self) -> float:
        if not self.samples:
            return 0.0
        return sum(s.cpu_user for s in self.samples) / len(self.samples)

    def avg_cpu_sys(self) -> float:
        if not self.samples:
            return 0.0
        return sum(s.cpu_sys for s in self.samples) / len(self.samples)

    def summary(self) -> dict:
        return {
            "label": self.label,
            "samples": len(self.samples),
            "avg_memory_kb": round(self.avg_memory_kb(), 2),
            "avg_cpu_user": round(self.avg_cpu_user(), 4),
            "avg_cpu_sys": round(self.avg_cpu_sys(), 4),
        }


def profile_command(label: str, cmd: str, iterations: int = 1) -> ProfileResult:
    """Run a shell command and collect resource usage samples."""
    import subprocess

    result = ProfileResult(label=label)
    for _ in range(iterations):
        usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        t0 = time.perf_counter()
        subprocess.run(cmd, shell=True, capture_output=True)
        elapsed = time.perf_counter() - t0
        usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)

        sample = ProfileSample(
            elapsed=elapsed,
            peak_memory_kb=usage_after.ru_maxrss,
            cpu_user=max(0.0, usage_after.ru_utime - usage_before.ru_utime),
            cpu_sys=max(0.0, usage_after.ru_stime - usage_before.ru_stime),
        )
        result.samples.append(sample)
    return result


def format_profile(result: ProfileResult) -> str:
    s = result.summary()
    lines = [
        f"Profile: {s['label']}",
        f"  Samples     : {s['samples']}",
        f"  Avg Memory  : {s['avg_memory_kb']} KB",
        f"  Avg CPU user: {s['avg_cpu_user']} s",
        f"  Avg CPU sys : {s['avg_cpu_sys']} s",
    ]
    return "\n".join(lines)
