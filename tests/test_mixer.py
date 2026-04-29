"""Tests for batchmark.mixer."""
from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.mixer import (
    MixedBatch,
    MixResult,
    mix,
    format_mix_summary,
)


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times, rc: int = 0) -> BatchResult:
    return BatchResult(label=label, runs=[_run(t, rc) for t in times])


# ---------------------------------------------------------------------------
# mix()
# ---------------------------------------------------------------------------

def test_mix_empty_sources_raises():
    with pytest.raises(ValueError, match="at least one source"):
        mix({})


def test_mix_invalid_ratio_raises():
    src = {"a": [make_batch("x", [1.0])]}
    with pytest.raises(ValueError, match="ratio"):
        mix(src, ratio=0.0)


def test_mix_single_source_returns_all_runs():
    src = {"a": [make_batch("cmd1", [1.0, 2.0, 3.0])]}
    result = mix(src)
    assert result.count == 1
    assert result.get("cmd1").total == 3


def test_mix_two_sources_same_label_combines_runs():
    src = {
        "a": [make_batch("cmd1", [1.0, 2.0])],
        "b": [make_batch("cmd1", [3.0, 4.0])],
    }
    result = mix(src)
    mb = result.get("cmd1")
    assert mb is not None
    assert mb.total == 4


def test_mix_sources_recorded():
    src = {
        "alpha": [make_batch("cmd1", [1.0])],
        "beta": [make_batch("cmd1", [2.0])],
    }
    mb = mix(src).get("cmd1")
    assert "alpha" in mb.sources
    assert "beta" in mb.sources


def test_mix_separate_labels_produce_separate_batches():
    src = {"a": [make_batch("x", [1.0]), make_batch("y", [2.0])]}
    result = mix(src)
    assert result.count == 2
    assert result.get("x") is not None
    assert result.get("y") is not None


def test_mix_ratio_reduces_run_count():
    src = {"a": [make_batch("cmd1", [float(i) for i in range(20)])]}
    result = mix(src, ratio=0.5, seed=42)
    mb = result.get("cmd1")
    assert mb.total <= 10
    assert mb.total >= 1


def test_mix_seed_reproducible():
    src = {"a": [make_batch("cmd1", [float(i) for i in range(20)])]}
    r1 = mix(src, ratio=0.5, seed=7)
    r2 = mix(src, ratio=0.5, seed=7)
    times1 = [r.elapsed for r in r1.get("cmd1").runs]
    times2 = [r.elapsed for r in r2.get("cmd1").runs]
    assert times1 == times2


def test_mix_labels_filter():
    src = {"a": [make_batch("x", [1.0]), make_batch("y", [2.0])]}
    result = mix(src, labels=["x"])
    assert result.count == 1
    assert result.get("x") is not None
    assert result.get("y") is None


def test_mix_success_count():
    src = {
        "a": [make_batch("cmd1", [1.0, 2.0], rc=0)],
        "b": [make_batch("cmd1", [3.0], rc=1)],
    }
    mb = mix(src).get("cmd1")
    assert mb.success_count == 2
    assert mb.total == 3


# ---------------------------------------------------------------------------
# format_mix_summary()
# ---------------------------------------------------------------------------

def test_format_mix_summary_contains_label():
    src = {"a": [make_batch("my-cmd", [1.0, 2.0])]}
    result = mix(src)
    summary = format_mix_summary(result)
    assert "my-cmd" in summary


def test_format_mix_summary_contains_run_count():
    src = {"a": [make_batch("cmd1", [1.0, 2.0, 3.0])]}
    result = mix(src)
    summary = format_mix_summary(result)
    assert "3 runs" in summary
