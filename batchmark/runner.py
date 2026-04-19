import subprocess
import time
from dataclasses import dataclass, field
from typing import List


@dataclass
class RunResult:
    command: str
    exit_code: int
    elapsed: float  # seconds
    stdout: str
    stderr: str


@dataclass
class BatchResult:
    command: str
    runs: List[RunResult] = field(default_factory=list)

    @property
    def times(self) -> List[float]:
        return [r.elapsed for r in self.runs]

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.exit_code == 0)


def run_command(command: str, shell: bool = True) -> RunResult:
    """Execute a single shell command and return timing + result."""
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
        )
        elapsed = time.perf_counter() - start
        return RunResult(
            command=command,
            exit_code=proc.returncode,
            elapsed=elapsed,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return RunResult(
            command=command,
            exit_code=-1,
            elapsed=elapsed,
            stdout="",
            stderr=str(exc),
        )


def benchmark_command(command: str, iterations: int = 5) -> BatchResult:
    """Run a command multiple times and collect results."""
    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    batch = BatchResult(command=command)
    for _ in range(iterations):
        batch.runs.append(run_command(command))
    return batch
