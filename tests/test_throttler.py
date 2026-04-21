"""Tests for batchmark.throttler."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from batchmark.runner import BatchResult, RunResult
from batchmark.throttler import (
    ThrottleConfig,
    ThrottledResult,
    throttle_benchmark,
    format_throttle_summary,
)


def _make_run(elapsed: float = 0.1, exit_code: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, stdout="", stderr="", exit_code=exit_code)


def fake_benchmark(command: str, label: str, iterations: int) -> BatchResult:
    runs = [_make_run(0.1 * (i + 1)) for i in range(iterations)]
    return BatchResult(label=label, runs=runs)


# ---------------------------------------------------------------------------
# throttle_benchmark – basic behaviour
# ---------------------------------------------------------------------------

def test_throttle_returns_all_runs():
    cfg = ThrottleConfig(delay_seconds=0.0, burst=2, cooldown_seconds=0.0)
    result = throttle_benchmark("echo hi", "echo", 5, cfg, fake_benchmark)
    assert len(result.batch.runs) == 5


def test_throttle_label_preserved():
    cfg = ThrottleConfig(delay_seconds=0.0, burst=3, cooldown_seconds=0.0)
    result = throttle_benchmark("echo hi", "my-label", 3, cfg, fake_benchmark)
    assert result.batch.label == "my-label"


def test_throttle_single_burst_no_pauses():
    cfg = ThrottleConfig(delay_seconds=0.0, burst=10, cooldown_seconds=0.0)
    result = throttle_benchmark("echo", "x", 4, cfg, fake_benchmark)
    assert result.pauses == 0
    assert result.total_delay_seconds == 0.0


def test_throttle_multiple_bursts_counts_pauses():
    cfg = ThrottleConfig(delay_seconds=0.0, burst=2, cooldown_seconds=0.0)
    result = throttle_benchmark("echo", "x", 6, cfg, fake_benchmark)
    # 3 bursts → 2 inter-burst pauses (cooldown only, delay=0)
    assert result.pauses == 2


def test_throttle_delay_accumulates():
    cfg = ThrottleConfig(delay_seconds=0.1, burst=1, cooldown_seconds=0.0)
    result = throttle_benchmark("echo", "x", 3, cfg, fake_benchmark)
    # 2 delay pauses between 3 single-run bursts
    assert abs(result.total_delay_seconds - 0.2) < 1e-9


def test_throttle_cooldown_accumulates():
    cfg = ThrottleConfig(delay_seconds=0.0, burst=1, cooldown_seconds=0.5)
    result = throttle_benchmark("echo", "x", 3, cfg, fake_benchmark)
    assert abs(result.total_delay_seconds - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------

def test_throttle_invalid_iterations_raises():
    cfg = ThrottleConfig()
    with pytest.raises(ValueError, match="iterations"):
        throttle_benchmark("echo", "x", 0, cfg, fake_benchmark)


def test_throttle_invalid_burst_raises():
    cfg = ThrottleConfig(burst=0)
    with pytest.raises(ValueError, match="burst"):
        throttle_benchmark("echo", "x", 1, cfg, fake_benchmark)


# ---------------------------------------------------------------------------
# sleep is actually called
# ---------------------------------------------------------------------------

def test_throttle_calls_sleep_for_delay():
    cfg = ThrottleConfig(delay_seconds=0.3, burst=1, cooldown_seconds=0.0)
    with patch("batchmark.throttler.time.sleep") as mock_sleep:
        throttle_benchmark("echo", "x", 2, cfg, fake_benchmark)
    calls = [c.args[0] for c in mock_sleep.call_args_list]
    assert 0.3 in calls


# ---------------------------------------------------------------------------
# format_throttle_summary
# ---------------------------------------------------------------------------

def test_format_throttle_summary_contains_label():
    cfg = ThrottleConfig(delay_seconds=0.0, burst=5, cooldown_seconds=0.0)
    result = throttle_benchmark("echo", "bench-label", 5, cfg, fake_benchmark)
    summary = format_throttle_summary(result)
    assert "bench-label" in summary


def test_format_throttle_summary_contains_run_count():
    cfg = ThrottleConfig(delay_seconds=0.0, burst=5, cooldown_seconds=0.0)
    result = throttle_benchmark("echo", "x", 4, cfg, fake_benchmark)
    summary = format_throttle_summary(result)
    assert "runs=4" in summary


def test_format_throttle_summary_contains_pauses():
    cfg = ThrottleConfig(delay_seconds=0.0, burst=2, cooldown_seconds=0.1)
    result = throttle_benchmark("echo", "x", 4, cfg, fake_benchmark)
    summary = format_throttle_summary(result)
    assert "pauses=" in summary
