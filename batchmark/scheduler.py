"""Scheduling strategies for running benchmark batches."""

from typing import List, Callable, Optional
from batchmark.runner import BatchResult, benchmark_command


def sequential(commands: List[str], iterations: int = 5, timeout: Optional[float] = None) -> List[BatchResult]:
    """Run each command sequentially."""
    return [benchmark_command(cmd, iterations=iterations, timeout=timeout) for cmd in commands]


def interleaved(commands: List[str], iterations: int = 5, timeout: Optional[float] = None) -> List[BatchResult]:
    """Run one iteration of each command in round-robin fashion."""
    from batchmark.runner import run_command, RunResult

    buckets: dict = {cmd: [] for cmd in commands}

    for _ in range(iterations):
        for cmd in commands:
            result = run_command(cmd, timeout=timeout)
            buckets[cmd].append(result)

    return [
        BatchResult(label=cmd, runs=buckets[cmd])
        for cmd in commands
    ]


def run_with_strategy(
    commands: List[str],
    strategy: str = "sequential",
    iterations: int = 5,
    timeout: Optional[float] = None,
) -> List[BatchResult]:
    """Dispatch to the chosen scheduling strategy."""
    strategies: dict = {
        "sequential": sequential,
        "interleaved": interleaved,
    }
    if strategy not in strategies:
        raise ValueError(f"Unknown strategy '{strategy}'. Choose from: {list(strategies)}")
    return strategies[strategy](commands, iterations=iterations, timeout=timeout)
