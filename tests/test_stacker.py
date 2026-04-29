"""Tests for batchmark.stacker."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.stacker import StackedLayer, StackResult, format_stack, stack


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times, rcs=None) -> BatchResult:
    if rcs is None:
        rcs = [0] * len(times)
    runs = [_run(t, rc) for t, rc in zip(times, rcs)]
    return BatchResult(label=label, runs=runs)


# ---------------------------------------------------------------------------
# stack()
# ---------------------------------------------------------------------------

def test_stack_empty_raises():
    with pytest.raises(ValueError):
        stack({})


def test_stack_single_source_single_batch():
    batches = [make_batch("cmd_a", [1.0, 2.0, 3.0])]
    result = stack({"src": batches})
    assert len(result.layers) == 1


def test_stack_source_name_stored():
    batches = [make_batch("cmd_a", [1.0, 2.0])]
    result = stack({"my_source": batches})
    assert result.layers[0].source == "my_source"


def test_stack_label_stored():
    batches = [make_batch("cmd_a", [1.0, 2.0])]
    result = stack({"src": batches})
    assert result.layers[0].label == "cmd_a"


def test_stack_mean_correct():
    batches = [make_batch("cmd_a", [1.0, 3.0])]
    result = stack({"src": batches})
    assert result.layers[0].mean == pytest.approx(2.0)


def test_stack_success_count():
    batches = [make_batch("cmd_a", [1.0, 2.0, 3.0], rcs=[0, 1, 0])]
    result = stack({"src": batches})
    assert result.layers[0].success_count == 2


def test_stack_success_rate():
    batches = [make_batch("cmd_a", [1.0, 2.0, 3.0, 4.0], rcs=[0, 0, 1, 0])]
    result = stack({"src": batches})
    assert result.layers[0].success_rate == pytest.approx(0.75)


def test_stack_multiple_sources():
    src_a = [make_batch("cmd", [1.0, 2.0])]
    src_b = [make_batch("cmd", [3.0, 4.0])]
    result = stack({"a": src_a, "b": src_b})
    assert len(result.layers) == 2
    assert {lyr.source for lyr in result.layers} == {"a", "b"}


def test_stack_sources_list_correct():
    result = stack({"x": [make_batch("l", [1.0])], "y": [make_batch("l", [2.0])]})
    assert result.sources == ["x", "y"]


def test_stack_labels_unique():
    batches = [make_batch("cmd_a", [1.0]), make_batch("cmd_b", [2.0])]
    result = stack({"src": batches})
    assert result.labels == ["cmd_a", "cmd_b"]


def test_stack_by_label():
    src_a = [make_batch("cmd", [1.0])]
    src_b = [make_batch("cmd", [2.0])]
    result = stack({"a": src_a, "b": src_b})
    layers = result.by_label("cmd")
    assert len(layers) == 2


def test_stack_by_source():
    batches = [make_batch("cmd_a", [1.0]), make_batch("cmd_b", [2.0])]
    result = stack({"src": batches})
    layers = result.by_source("src")
    assert len(layers) == 2


def test_stack_empty_batch_mean_zero():
    batch = BatchResult(label="empty", runs=[])
    result = stack({"src": [batch]})
    assert result.layers[0].mean == 0.0


# ---------------------------------------------------------------------------
# format_stack()
# ---------------------------------------------------------------------------

def test_format_stack_contains_label():
    batches = [make_batch("my_cmd", [1.0, 2.0])]
    result = stack({"src": batches})
    output = format_stack(result)
    assert "my_cmd" in output


def test_format_stack_contains_source():
    batches = [make_batch("cmd", [1.0])]
    result = stack({"alpha": batches})
    output = format_stack(result)
    assert "alpha" in output


def test_format_stack_contains_header():
    batches = [make_batch("cmd", [1.0])]
    result = stack({"src": batches})
    output = format_stack(result)
    assert "Mean" in output
    assert "Stdev" in output
