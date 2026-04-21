"""Tests for batchmark.grouper."""

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.grouper import (
    GroupedBatches,
    group_by_key,
    group_by_prefix,
    group_by_label,
    format_grouped,
)


def make_batch(label: str, n: int = 3) -> BatchResult:
    runs = [RunResult(elapsed=0.1 * i, returncode=0) for i in range(1, n + 1)]
    return BatchResult(label=label, runs=runs)


# --- group_by_key ---

def test_group_by_key_basic():
    batches = [make_batch("a"), make_batch("b"), make_batch("a")]
    result = group_by_key(batches, lambda b: b.label)
    assert set(result.keys()) == {"a", "b"}
    assert len(result.get("a")) == 2
    assert len(result.get("b")) == 1


def test_group_by_key_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        group_by_key([], lambda b: b.label)


def test_group_by_key_single_batch():
    batches = [make_batch("solo")]
    result = group_by_key(batches, lambda b: b.label)
    assert result.size() == 1
    assert result.get("solo")[0].label == "solo"


# --- group_by_prefix ---

def test_group_by_prefix_splits_on_colon():
    batches = [
        make_batch("python:fast"),
        make_batch("python:slow"),
        make_batch("node:fast"),
    ]
    result = group_by_prefix(batches)
    assert set(result.keys()) == {"python", "node"}
    assert len(result.get("python")) == 2


def test_group_by_prefix_no_sep_uses_full_label():
    batches = [make_batch("nocolon"), make_batch("also_no_colon")]
    result = group_by_prefix(batches)
    assert "nocolon" in result.keys()
    assert "also_no_colon" in result.keys()


def test_group_by_prefix_custom_sep():
    batches = [make_batch("a/b"), make_batch("a/c"), make_batch("d/e")]
    result = group_by_prefix(batches, sep="/")
    assert set(result.keys()) == {"a", "d"}


# --- group_by_label ---

def test_group_by_label_each_label_is_own_group():
    batches = [make_batch("x"), make_batch("y"), make_batch("z")]
    result = group_by_label(batches)
    assert result.size() == 3


def test_group_by_label_duplicate_labels_merged():
    batches = [make_batch("dup"), make_batch("dup")]
    result = group_by_label(batches)
    assert result.size() == 1
    assert len(result.get("dup")) == 2


# --- format_grouped ---

def test_format_grouped_contains_key():
    batches = [make_batch("grp:a"), make_batch("grp:b")]
    grouped = group_by_prefix(batches)
    text = format_grouped(grouped)
    assert "[grp]" in text


def test_format_grouped_contains_labels():
    batches = [make_batch("grp:alpha")]
    grouped = group_by_prefix(batches)
    text = format_grouped(grouped)
    assert "grp:alpha" in text


def test_format_grouped_shows_batch_count():
    batches = [make_batch("g:1"), make_batch("g:2"), make_batch("g:3")]
    grouped = group_by_prefix(batches)
    text = format_grouped(grouped)
    assert "3 batch" in text
