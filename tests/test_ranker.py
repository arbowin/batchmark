import pytest
from batchmark.runner import BatchResult
from batchmark.ranker import rank, format_ranking, RankingResult


def make_batch(label: str, times, successes=None):
    total = len(times)
    if successes is None:
        successes = total
    return BatchResult(label=label, times=times, total=total, successes=successes)


def test_rank_orders_by_mean():
    batches = [
        make_batch("slow", [2.0, 2.1, 1.9]),
        make_batch("fast", [0.5, 0.6, 0.4]),
    ]
    result = rank(batches)
    assert result.entries[0].label == "fast"
    assert result.entries[1].label == "slow"


def test_rank_assigns_ranks():
    batches = [
        make_batch("a", [1.0, 1.0]),
        make_batch("b", [2.0, 2.0]),
        make_batch("c", [3.0, 3.0]),
    ]
    result = rank(batches)
    ranks = [e.rank for e in result.entries]
    assert ranks == [1, 2, 3]


def test_rank_best_and_worst():
    batches = [
        make_batch("x", [1.0]),
        make_batch("y", [5.0]),
    ]
    result = rank(batches)
    assert result.best().label == "x"
    assert result.worst().label == "y"


def test_rank_penalizes_low_success_rate():
    batches = [
        make_batch("unreliable", [0.1, 0.1, 0.1], successes=1),
        make_batch("reliable", [1.0, 1.0, 1.0], successes=3),
    ]
    result = rank(batches)
    assert result.entries[0].label == "reliable"


def test_rank_empty_raises():
    with pytest.raises(ValueError):
        rank([])


def test_rank_single_entry():
    batches = [make_batch("only", [1.0, 2.0])]
    result = rank(batches)
    assert len(result.entries) == 1
    assert result.entries[0].rank == 1


def test_rank_success_rate_stored():
    batches = [make_batch("half", [1.0, 1.0, 1.0, 1.0], successes=2)]
    result = rank(batches)
    assert result.entries[0].success_rate == pytest.approx(0.5)


def test_format_ranking_contains_label():
    batches = [make_batch("cmd_a", [1.0, 1.2])]
    result = rank(batches)
    output = format_ranking(result)
    assert "cmd_a" in output


def test_format_ranking_contains_rank_header():
    batches = [make_batch("cmd_a", [1.0])]
    result = rank(batches)
    output = format_ranking(result)
    assert "Rank" in output


def test_format_ranking_multiple_entries():
    batches = [
        make_batch("alpha", [1.0]),
        make_batch("beta", [2.0]),
    ]
    result = rank(batches)
    output = format_ranking(result)
    assert "alpha" in output
    assert "beta" in output
