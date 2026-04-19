import pytest
from batchmark.runner import run_command, benchmark_command
from batchmark.stats import mean, median, stdev, summarize


# --- runner tests ---

def test_run_command_success():
    result = run_command("echo hello")
    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.elapsed >= 0


def test_run_command_failure():
    result = run_command("exit 1", shell=True)
    assert result.exit_code != 0


def test_benchmark_command_returns_correct_count():
    batch = benchmark_command("echo x", iterations=3)
    assert len(batch.runs) == 3
    assert batch.command == "echo x"


def test_benchmark_command_success_count():
    batch = benchmark_command("echo x", iterations=4)
    assert batch.success_count == 4


def test_benchmark_command_invalid_iterations():
    with pytest.raises(ValueError):
        benchmark_command("echo x", iterations=0)


def test_batch_result_times_length():
    batch = benchmark_command("echo x", iterations=3)
    assert len(batch.times) == 3


# --- stats tests ---

def test_mean():
    assert mean([1.0, 2.0, 3.0]) == pytest.approx(2.0)


def test_median_odd():
    assert median([3.0, 1.0, 2.0]) == pytest.approx(2.0)


def test_median_even():
    assert median([1.0, 2.0, 3.0, 4.0]) == pytest.approx(2.5)


def test_stdev_single():
    assert stdev([5.0]) == 0.0


def test_stdev_known():
    assert stdev([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]) == pytest.approx(2.0)


def test_summarize_keys():
    summary = summarize([1.0, 2.0, 3.0])
    assert set(summary.keys()) == {"min", "max", "mean", "median", "stdev", "count"}


def test_mean_empty_raises():
    with pytest.raises(ValueError):
        mean([])
