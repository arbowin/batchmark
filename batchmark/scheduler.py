"""Scheduling strategies for running benchmark batches."""

from typing import List, Callable, Optional
from batchmark.runner import BatchResult, benchmark_command


def sequential(commands: List[str], iterations: int = 5, timeout: Optional[float] = None) -> List[BatchResult]:
    """Run each command sequentially, completing all iterations before moving to the next."""
    return [benchmark_command(cmd, iterations=iterations, timeout=timeout) for cmd in commands]


def interleaved(commands: List[str], iterations: int = 5, timeout: Optional[float] = None) -> List[BatchResult]:
    """Run one iteration of each command in round-robin fashion.

    This reduces the impact of system-level fluctuations by interleaving
    iterations across all commands rather than running each command in isolation.
    """
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
    """Dispatch to the chosen scheduling strategy.

    Args:
        commands: List of shell commands to benchmark.
        strategy: One of 'sequential' or 'interleaved'.
        iterations: Number of times each command is run.
        timeout: Optional per-run timeout in seconds.

    Returns:
        A list of BatchResult objects, one per command.

    Raises:
        ValueError: If an unrecognised strategy name is provided.
        ValueError: If commands list is empty.
    """
    if not commands:
        raise ValueError("commands list must not be empty")

    strategies: dict = {
        "sequential": sequential,
        "interleaved": interleaved,
    }
    if strategy not in strategies:
        raise ValueError(f"Unknown strategy '{strategy}'. Choose from: {list(strategies)}")
    return strategies[strategy](commands, iterations=iterations, timeout=timeout)
