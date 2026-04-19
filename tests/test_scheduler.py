"""Tests for batchmark.scheduler module."""

import pytest
from unittest.mock import patch, MagicMock
from batchmark.runner import RunResult, BatchResult
from batchmark.scheduler import sequential, interleaved, run_with_strategy


def make_run(duration=0.1, success=True):
    return RunResult(duration=duration, success=success, stdout="", stderr="")


def fake_benchmark(cmd, iterations=5, timeout=None):
    return BatchResult(label=cmd, runs=[make_run() for _ in range(iterations)])


def fake_run_command(cmd, timeout=None):
    return make_run()


@patch("batchmark.scheduler.benchmark_command", side_effect=fake_benchmark)
def test_sequential_returns_all(mock_bm):
    results = sequential(["echo a", "echo b"], iterations=3)
    assert len(results) == 2
    assert results[0].label == "echo a"
    assert results[1].label == "echo b"


@patch("batchmark.scheduler.benchmark_command", side_effect=fake_benchmark)
def test_sequential_iteration_count(mock_bm):
    results = sequential(["cmd"], iterations=4)
    assert len(results[0].runs) == 4


@patch("batchmark.scheduler.run_command", side_effect=fake_run_command)
def test_interleaved_returns_all(mock_rc):
    results = interleaved(["echo a", "echo b"], iterations=3)
    assert len(results) == 2


@patch("batchmark.scheduler.run_command", side_effect=fake_run_command)
def test_interleaved_iteration_count(mock_rc):
    results = interleaved(["cmd"], iterations=5)
    assert len(results[0].runs) == 5


@patch("batchmark.scheduler.run_command", side_effect=fake_run_command)
def test_interleaved_call_order(mock_rc):
    interleaved(["a", "b"], iterations=2)
    calls = [c.args[0] for c in mock_rc.call_args_list]
    assert calls == ["a", "b", "a", "b"]


@patch("batchmark.scheduler.benchmark_command", side_effect=fake_benchmark)
def test_run_with_strategy_sequential(mock_bm):
    results = run_with_strategy(["ls"], strategy="sequential", iterations=2)
    assert len(results) == 1


@patch("batchmark.scheduler.run_command", side_effect=fake_run_command)
def test_run_with_strategy_interleaved(mock_rc):
    results = run_with_strategy(["ls"], strategy="interleaved", iterations=2)
    assert len(results) == 1


def test_run_with_strategy_invalid():
    with pytest.raises(ValueError, match="Unknown strategy"):
        run_with_strategy(["ls"], strategy="random")
