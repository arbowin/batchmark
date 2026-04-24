"""Stream benchmark results incrementally, emitting each BatchResult as it completes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, List, Optional

from batchmark.runner import BatchResult, benchmark_command


@dataclass
class StreamConfig:
    commands: List[str]
    labels: List[str]
    iterations: int = 5
    on_result: Optional[Callable[[BatchResult], None]] = None


@dataclass
class StreamSession:
    config: StreamConfig
    results: List[BatchResult] = field(default_factory=list)
    completed: int = 0

    @property
    def total(self) -> int:
        return len(self.config.commands)

    @property
    def progress(self) -> float:
        if self.total == 0:
            return 0.0
        return self.completed / self.total


def _validate(config: StreamConfig) -> None:
    if len(config.commands) != len(config.labels):
        raise ValueError("commands and labels must have the same length")
    if config.iterations < 1:
        raise ValueError("iterations must be >= 1")


def stream(config: StreamConfig) -> Iterator[BatchResult]:
    """Yield each BatchResult as it finishes benchmarking."""
    _validate(config)
    for cmd, label in zip(config.commands, config.labels):
        result = benchmark_command(cmd, label=label, iterations=config.iterations)
        if config.on_result is not None:
            config.on_result(result)
        yield result


def collect_stream(config: StreamConfig) -> StreamSession:
    """Run the full stream and collect all results into a StreamSession."""
    session = StreamSession(config=config)
    for result in stream(config):
        session.results.append(result)
        session.completed += 1
    return session
