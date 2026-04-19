"""Tests for batchmark.annotator."""
import pytest
from unittest.mock import MagicMock
from batchmark.runner import BatchResult, RunResult
from batchmark.annotator import (
    annotate, build_index, by_note_keyword, format_annotated, AnnotatedResult
)


def make_batch(label="cmd", n=3):
    runs = [RunResult(returncode=0, elapsed=0.1 * i, stdout="", stderr="") for i in range(1, n + 1)]
    return BatchResult(label=label, runs=runs)


def test_annotate_stores_label():
    b = make_batch("echo hi")
    ar = annotate(b, ["fast", "stable"])
    assert ar.label == "echo hi"


def test_annotate_stores_notes():
    b = make_batch()
    ar = annotate(b, ["note one", "note two"])
    assert ar.notes == ["note one", "note two"]


def test_annotate_strips_whitespace():
    b = make_batch()
    ar = annotate(b, ["  padded  ", " also "])
    assert ar.notes == ["padded", "also"]


def test_annotate_skips_empty_notes():
    b = make_batch()
    ar = annotate(b, ["", "  ", "valid"])
    assert ar.notes == ["valid"]


def test_annotate_empty_notes():
    b = make_batch()
    ar = annotate(b, [])
    assert ar.notes == []


def test_build_index_contains_entries():
    results = [annotate(make_batch(f"cmd{i}"), [f"note{i}"]) for i in range(3)]
    idx = build_index(results)
    assert len(idx.entries) == 3


def test_by_note_keyword_finds_match():
    r1 = annotate(make_batch("a"), ["fast and reliable"])
    r2 = annotate(make_batch("b"), ["slow startup"])
    idx = build_index([r1, r2])
    found = by_note_keyword(idx, "fast")
    assert len(found) == 1
    assert found[0].label == "a"


def test_by_note_keyword_case_insensitive():
    r1 = annotate(make_batch("a"), ["FAST run"])
    idx = build_index([r1])
    found = by_note_keyword(idx, "fast")
    assert len(found) == 1


def test_by_note_keyword_no_match():
    r1 = annotate(make_batch("a"), ["nothing here"])
    idx = build_index([r1])
    assert by_note_keyword(idx, "xyz") == []


def test_format_annotated_contains_label():
    ar = annotate(make_batch("ls -la"), ["baseline"])
    out = format_annotated(ar)
    assert "ls -la" in out


def test_format_annotated_contains_notes():
    ar = annotate(make_batch("cmd"), ["note alpha", "note beta"])
    out = format_annotated(ar)
    assert "note alpha" in out
    assert "note beta" in out


def test_format_annotated_no_notes_message():
    ar = annotate(make_batch("cmd"), [])
    out = format_annotated(ar)
    assert "no notes" in out
