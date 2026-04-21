"""Throttler: rate-limit benchmark execution to avoid resource contention."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List

from batchmark.runner import BatchResult


@dataclass
class ThrottleConfig:
    """Configuration for throttled benchmark execution."""
    delay_seconds: float = 0.5          # pause between each command run
    burst: int = 1                       # how many runs before a pause
    cooldown_seconds: float = 0.0        # extra pause after each burst


@dataclass
class ThrottledResult:
    """Wraps a BatchResult with throttle metadata."""
    batch: BatchResult
    total_delay_seconds: float
    pauses: int


def _pause(seconds: float) -> None:
    """Sleep for the given number of seconds (no-op if <= 0)."""
    if seconds > 0:
        time.sleep(seconds)


def throttle_benchmark(
    command: str,
    label: str,
    iterations: int,
    config: ThrottleConfig,
    benchmark_fn: Callable[[str, str, int], BatchResult],
) -> ThrottledResult:
    """Run benchmark_fn in throttled bursts.

    Splits *iterations* into bursts of *config.burst* size, inserting
    delay_seconds between individual runs and cooldown_seconds between bursts.
    """
    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    if config.burst < 1:
        raise ValueError("burst must be >= 1")

    all_runs: List = []
    total_delay = 0.0
    pauses = 0
    remaining = iterations

    while remaining > 0:
        chunk = min(config.burst, remaining)
        result = benchmark_fn(command, label, chunk)
        all_runs.extend(result.runs)
        remaining -= chunk

        if remaining > 0:
            _pause(config.cooldown_seconds)
            total_delay += config.cooldown_seconds
            pauses += 1
        if remaining > 0 and config.delay_seconds > 0:
            _pause(config.delay_seconds)
            total_delay += config.delay_seconds
            pauses += 1

    merged = BatchResult(label=label, runs=all_runs)
    return ThrottledResult(batch=merged, total_delay_seconds=total_delay, pauses=pauses)


def format_throttle_summary(result: ThrottledResult) -> str:
    """Return a human-readable summary of throttle overhead."""
    b = result.batch
    return (
        f"[{b.label}] runs={len(b.runs)} "
        f"pauses={result.pauses} "
        f"total_delay={result.total_delay_seconds:.2f}s"
    )
