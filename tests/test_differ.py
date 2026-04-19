import pytest
from batchmark.runner import BatchResult, RunResult
from batchmark.differ import diff_batches, format_diff, DiffEntry


def make_batch(label, times, successes=None):
    if successes is None:
        successes = len(times)
    runs = [RunResult(elapsed=t, returncode=0, stdout='', stderr='') for t in times]
    return BatchResult(label=label, runs=runs)


def test_diff_returns_entry_for_common_labels():
    before = [make_batch('cmd_a', [1.0, 1.1, 0.9])]
    after = [make_batch('cmd_a', [1.2, 1.3, 1.1])]
    result = diff_batches(before, after)
    assert len(result.entries) == 1
    assert result.entries[0].label == 'cmd_a'


def test_diff_ignores_labels_not_in_both():
    before = [make_batch('only_before', [1.0])]
    after = [make_batch('only_after', [1.0])]
    result = diff_batches(before, after)
    assert result.entries == []


def test_diff_detects_regression():
    before = [make_batch('slow', [1.0, 1.0, 1.0])]
    after = [make_batch('slow', [2.0, 2.0, 2.0])]
    result = diff_batches(before, after)
    assert result.entries[0].verdict == 'regressed'


def test_diff_detects_improvement():
    before = [make_batch('fast', [2.0, 2.0, 2.0])]
    after = [make_batch('fast', [1.0, 1.0, 1.0])]
    result = diff_batches(before, after)
    assert result.entries[0].verdict == 'improved'


def test_diff_unchanged_within_threshold():
    before = [make_batch('stable', [1.000, 1.000])]
    after = [make_batch('stable', [1.001, 1.001])]
    result = diff_batches(before, after)
    assert result.entries[0].verdict == 'unchanged'


def test_regressions_filter():
    before = [make_batch('a', [1.0]), make_batch('b', [1.0])]
    after = [make_batch('a', [2.0]), make_batch('b', [1.0])]
    result = diff_batches(before, after)
    assert len(result.regressions()) == 1
    assert result.regressions()[0].label == 'a'


def test_improvements_filter():
    before = [make_batch('a', [2.0]), make_batch('b', [1.0])]
    after = [make_batch('a', [1.0]), make_batch('b', [1.0])]
    result = diff_batches(before, after)
    assert len(result.improvements()) == 1


def test_pct_change_correct():
    before = [make_batch('x', [1.0, 1.0])]
    after = [make_batch('x', [1.5, 1.5])]
    result = diff_batches(before, after)
    assert abs(result.entries[0].pct_change - 0.5) < 1e-6


def test_format_diff_contains_label():
    before = [make_batch('mycmd', [1.0, 1.0])]
    after = [make_batch('mycmd', [2.0, 2.0])]
    result = diff_batches(before, after)
    text = format_diff(result)
    assert 'mycmd' in text
    assert 'regressed' in text
