"""Tests for batchmark.aligner."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.aligner import (
    AlignResult,
    AlignedSource,
    align,
    format_alignment,
    _all_labels,
    _common_labels,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _run(elapsed: float = 0.1, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, n: int = 3) -> BatchResult:
    return BatchResult(label=label, runs=[_run() for _ in range(n)])


# ---------------------------------------------------------------------------
# _all_labels
# ---------------------------------------------------------------------------

def test_all_labels_preserves_order():
    src1 = [make_batch("a"), make_batch("b")]
    src2 = [make_batch("b"), make_batch("c")]
    assert _all_labels([src1, src2]) == ["a", "b", "c"]


def test_all_labels_single_source():
    src = [make_batch("x"), make_batch("y")]
    assert _all_labels([src]) == ["x", "y"]


# ---------------------------------------------------------------------------
# _common_labels
# ---------------------------------------------------------------------------

def test_common_labels_intersection():
    src1 = [make_batch("a"), make_batch("b")]
    src2 = [make_batch("b"), make_batch("c")]
    assert _common_labels([src1, src2]) == ["b"]


def test_common_labels_all_shared():
    src1 = [make_batch("a"), make_batch("b")]
    src2 = [make_batch("a"), make_batch("b")]
    assert set(_common_labels([src1, src2])) == {"a", "b"}


def test_common_labels_empty_sources():
    assert _common_labels([]) == []


# ---------------------------------------------------------------------------
# align()
# ---------------------------------------------------------------------------

def test_align_empty_sources_raises():
    with pytest.raises(ValueError, match="at least one source"):
        align([])


def test_align_mismatched_names_raises():
    src = [make_batch("a")]
    with pytest.raises(ValueError, match="len\\(names\\)"):
        align([src], names=["x", "y"])


def test_align_returns_align_result():
    src = [make_batch("a"), make_batch("b")]
    result = align([src])
    assert isinstance(result, AlignResult)


def test_align_all_labels_populated():
    src1 = [make_batch("a"), make_batch("b")]
    src2 = [make_batch("b"), make_batch("c")]
    result = align([src1, src2])
    assert set(result.all_labels) == {"a", "b", "c"}


def test_align_common_labels_populated():
    src1 = [make_batch("a"), make_batch("b")]
    src2 = [make_batch("b"), make_batch("c")]
    result = align([src1, src2])
    assert result.common_labels == ["b"]


def test_align_fill_missing_adds_placeholder():
    src1 = [make_batch("a"), make_batch("b")]
    src2 = [make_batch("b"), make_batch("c")]
    result = align([src1, src2], fill_missing=True)
    # src1 should have a placeholder for "c"
    assert "c" in result.sources[0].batches
    assert result.sources[0].batches["c"].runs == []


def test_align_fill_missing_false_does_not_insert():
    src1 = [make_batch("a")]
    src2 = [make_batch("a"), make_batch("b")]
    result = align([src1, src2], fill_missing=False)
    assert "b" not in result.sources[0].batches
    assert "b" in result.sources[0].missing_labels


def test_align_missing_labels_recorded():
    src1 = [make_batch("a")]
    src2 = [make_batch("a"), make_batch("b")]
    result = align([src1, src2])
    assert "b" in result.sources[0].missing_labels


def test_align_custom_names():
    src = [make_batch("a")]
    result = align([src], names=["run-A"])
    assert result.sources[0].name == "run-A"


def test_align_default_names():
    src1 = [make_batch("a")]
    src2 = [make_batch("a")]
    result = align([src1, src2])
    assert result.sources[0].name == "source-0"
    assert result.sources[1].name == "source-1"


# ---------------------------------------------------------------------------
# format_alignment()
# ---------------------------------------------------------------------------

def test_format_alignment_contains_source_count():
    src1 = [make_batch("a")]
    src2 = [make_batch("a"), make_batch("b")]
    result = align([src1, src2], names=["alpha", "beta"])
    text = format_alignment(result)
    assert "2 source(s)" in text


def test_format_alignment_contains_all_labels():
    src1 = [make_batch("fast")]
    src2 = [make_batch("fast"), make_batch("slow")]
    result = align([src1, src2])
    text = format_alignment(result)
    assert "fast" in text
    assert "slow" in text


def test_format_alignment_shows_missing():
    src1 = [make_batch("a")]
    src2 = [make_batch("a"), make_batch("b")]
    result = align([src1, src2])
    text = format_alignment(result)
    assert "b" in text
