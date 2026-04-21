"""Tests for batchmark.replayer and batchmark.replay_cli."""

import json
import os
import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.snapshot import save_snapshot, Snapshot
from batchmark.replayer import (
    ReplayResult,
    ReplaySession,
    _replay_batch,
    replay,
    format_replay,
)


def make_batch(label: str, times, successes=None) -> BatchResult:
    if successes is None:
        successes = [True] * len(times)
    runs = [RunResult(elapsed=t, success=s, returncode=0 if s else 1) for t, s in zip(times, successes)]
    return BatchResult(label=label, runs=runs)


def make_snapshot(tmp_path, batches) -> str:
    path = str(tmp_path / "snap.json")
    snap = Snapshot(name="test-snap", batches=batches)
    save_snapshot(snap, path)
    return path


# --- _replay_batch ---

def test_replay_batch_label():
    b = make_batch("cmd-a", [0.1, 0.2, 0.3])
    r = _replay_batch(b, "s1")
    assert r.label == "cmd-a"


def test_replay_batch_source_snapshot():
    b = make_batch("cmd-a", [0.1, 0.2])
    r = _replay_batch(b, "my-snap")
    assert r.source_snapshot == "my-snap"


def test_replay_batch_total():
    b = make_batch("x", [0.1, 0.2, 0.3])
    r = _replay_batch(b, "s")
    assert r.total == 3


def test_replay_batch_success_count():
    b = make_batch("x", [0.1, 0.2, 0.3], successes=[True, False, True])
    r = _replay_batch(b, "s")
    assert r.success_count == 2


def test_replay_batch_mean():
    b = make_batch("x", [1.0, 3.0])
    r = _replay_batch(b, "s")
    assert r.mean == pytest.approx(2.0)


def test_replay_batch_empty_runs():
    b = BatchResult(label="empty", runs=[])
    r = _replay_batch(b, "s")
    assert r.total == 0
    assert r.mean == 0.0


# --- replay ---

def test_replay_returns_session(tmp_path):
    snap_path = make_snapshot(tmp_path, [make_batch("a", [0.5, 0.6])])
    session = replay(snap_path)
    assert isinstance(session, ReplaySession)
    assert session.snapshot_name == "test-snap"


def test_replay_all_labels(tmp_path):
    snap_path = make_snapshot(tmp_path, [
        make_batch("a", [0.1]),
        make_batch("b", [0.2]),
    ])
    session = replay(snap_path)
    labels = [r.label for r in session.results]
    assert "a" in labels and "b" in labels


def test_replay_filtered_labels(tmp_path):
    snap_path = make_snapshot(tmp_path, [
        make_batch("a", [0.1]),
        make_batch("b", [0.2]),
    ])
    session = replay(snap_path, labels=["a"])
    assert len(session.results) == 1
    assert session.results[0].label == "a"


def test_replay_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        replay("/nonexistent/path/snap.json")


# --- format_replay ---

def test_format_replay_contains_snapshot_name(tmp_path):
    snap_path = make_snapshot(tmp_path, [make_batch("cmd", [0.1])])
    session = replay(snap_path)
    text = format_replay(session)
    assert "test-snap" in text


def test_format_replay_contains_label(tmp_path):
    snap_path = make_snapshot(tmp_path, [make_batch("my-cmd", [0.1, 0.2])])
    session = replay(snap_path)
    text = format_replay(session)
    assert "my-cmd" in text


def test_format_replay_contains_mean(tmp_path):
    snap_path = make_snapshot(tmp_path, [make_batch("x", [1.0, 3.0])])
    session = replay(snap_path)
    text = format_replay(session)
    assert "mean" in text
