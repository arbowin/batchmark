"""Tests for batchmark.scorer."""
import pytest
from batchmark.runner import BatchResult, RunResult
from batchmark.scorer import score, score_all, format_scores, ScoredResult


def make_batch(label: str, times, failures=0) -> BatchResult:
    runs = [RunResult(elapsed=t, returncode=0, stdout="", stderr="") for t in times]
    runs += [RunResult(elapsed=0.1, returncode=1, stdout="", stderr="err") for _ in range(failures)]
    return BatchResult(label=label, runs=runs)


def test_score_returns_scored_result():
    b = make_batch("cmd", [1.0, 2.0, 3.0])
    result = score(b, baseline_mean=2.0)
    assert isinstance(result, ScoredResult)
    assert result.label == "cmd"


def test_score_mean_correct():
    b = make_batch("cmd", [1.0, 2.0, 3.0])
    result = score(b, baseline_mean=1.0)
    assert abs(result.mean - 2.0) < 1e-9


def test_score_full_success_rate():
    b = make_batch("cmd", [1.0, 1.0])
    result = score(b, baseline_mean=1.0)
    assert result.success_rate == 1.0


def test_score_partial_success_rate():
    b = make_batch("cmd", [1.0, 1.0], failures=2)
    result = score(b, baseline_mean=1.0)
    assert result.success_rate == 0.5


def test_score_zero_weights_raises():
    b = make_batch("cmd", [1.0])
    with pytest.raises(ValueError):
        score(b, time_weight=0.0, success_weight=0.0, baseline_mean=1.0)


def test_score_all_sorted_ascending():
    fast = make_batch("fast", [0.5, 0.5])
    slow = make_batch("slow", [5.0, 5.0])
    results = score_all([slow, fast])
    assert results[0].label == "fast"
    assert results[1].label == "slow"


def test_score_all_empty():
    assert score_all([]) == []


def test_score_all_single():
    b = make_batch("only", [1.0, 2.0])
    results = score_all([b])
    assert len(results) == 1
    assert results[0].label == "only"


def test_score_all_penalizes_failures():
    reliable = make_batch("reliable", [2.0, 2.0], failures=0)
    flaky = make_batch("flaky", [1.0, 1.0], failures=8)
    results = score_all([reliable, flaky], time_weight=0.3, success_weight=0.7)
    assert results[0].label == "reliable"


def test_format_scores_contains_label():
    b = make_batch("mycmd", [1.0, 2.0])
    scored = score_all([b])
    output = format_scores(scored)
    assert "mycmd" in output


def test_format_scores_empty():
    output = format_scores([])
    assert "No results" in output


def test_format_scores_rank_column():
    b1 = make_batch("a", [1.0])
    b2 = make_batch("b", [2.0])
    output = format_scores(score_all([b1, b2]))
    assert "1" in output
    assert "2" in output
