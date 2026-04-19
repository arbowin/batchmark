"""Tests for batchmark.history."""
import json
import os
import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.history import (
    History,
    HistoryEntry,
    entry_from_batch,
    load_history,
    save_history,
    append_batch,
)


def make_batch(label="cmd", times=None, successes=None):
    times = times or [1.0, 2.0, 3.0]
    successes = successes if successes is not None else [True] * len(times)
    results = [RunResult(elapsed=t, returncode=0 if s else 1, stdout="", stderr="") for t, s in zip(times, successes)]
    return BatchResult(label=label, results=results)


def test_entry_from_batch_label():
    batch = make_batch(label="echo")
    entry = entry_from_batch(batch)
    assert entry.label == "echo"


def test_entry_from_batch_stats():
    batch = make_batch(times=[1.0, 2.0, 3.0])
    entry = entry_from_batch(batch)
    assert entry.mean == pytest.approx(2.0)
    assert entry.median == pytest.approx(2.0)
    assert entry.total == 3


def test_entry_from_batch_success_count():
    batch = make_batch(times=[1.0, 2.0, 3.0], successes=[True, False, True])
    entry = entry_from_batch(batch)
    assert entry.success_count == 2


def test_entry_timestamp_set():
    batch = make_batch()
    entry = entry_from_batch(batch, timestamp="2024-01-01T00:00:00+00:00")
    assert entry.timestamp == "2024-01-01T00:00:00+00:00"


def test_load_history_missing_file(tmp_path):
    h = load_history(str(tmp_path / "nonexistent.json"))
    assert h.entries == []


def test_save_and_load_history(tmp_path):
    path = str(tmp_path / "history.json")
    entry = HistoryEntry(label="x", timestamp="ts", mean=1.0, median=1.0, stdev=0.0, success_count=3, total=3)
    h = History(entries=[entry])
    save_history(h, path)
    loaded = load_history(path)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].label == "x"
    assert loaded.entries[0].mean == 1.0


def test_append_batch_creates_file(tmp_path):
    path = str(tmp_path / "sub" / "history.json")
    batch = make_batch(label="ls")
    append_batch(batch, path)
    assert os.path.exists(path)


def test_append_batch_accumulates(tmp_path):
    path = str(tmp_path / "history.json")
    append_batch(make_batch(label="a"), path)
    append_batch(make_batch(label="b"), path)
    h = load_history(path)
    assert len(h.entries) == 2
    assert h.entries[0].label == "a"
    assert h.entries[1].label == "b"


def test_save_history_json_structure(tmp_path):
    path = str(tmp_path / "history.json")
    entry = HistoryEntry(label="z", timestamp="ts", mean=0.5, median=0.5, stdev=0.1, success_count=1, total=1)
    save_history(History(entries=[entry]), path)
    with open(path) as f:
        data = json.load(f)
    assert "entries" in data
    assert data["entries"][0]["label"] == "z"
