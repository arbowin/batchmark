"""Tests for batchmark.replay_cli."""

import json
import sys
import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.snapshot import save_snapshot, Snapshot
from batchmark.replay_cli import build_replay_parser, main


def make_batch(label: str, times):
    runs = [RunResult(elapsed=t, success=True, returncode=0) for t in times]
    return BatchResult(label=label, runs=runs)


def make_snapshot(tmp_path, batches, name="cli-snap") -> str:
    path = str(tmp_path / "snap.json")
    snap = Snapshot(name=name, batches=batches)
    save_snapshot(snap, path)
    return path


# --- parser ---

def test_build_replay_parser_defaults():
    parser = build_replay_parser()
    args = parser.parse_args(["snap.json"])
    assert args.snapshot == "snap.json"
    assert args.labels is None
    assert args.output_format == "text"


def test_build_replay_parser_labels():
    parser = build_replay_parser()
    args = parser.parse_args(["snap.json", "--labels", "a", "b"])
    assert args.labels == ["a", "b"]


def test_build_replay_parser_json_format():
    parser = build_replay_parser()
    args = parser.parse_args(["snap.json", "--format", "json"])
    assert args.output_format == "json"


# --- main text output ---

def test_main_text_output(tmp_path, capsys):
    path = make_snapshot(tmp_path, [make_batch("hello", [0.1, 0.2])])
    main([path])
    captured = capsys.readouterr()
    assert "hello" in captured.out


def test_main_json_output(tmp_path, capsys):
    path = make_snapshot(tmp_path, [make_batch("cmd", [0.5, 1.5])])
    main([path, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["label"] == "cmd"
    assert "mean" in data[0]


def test_main_json_multiple_batches(tmp_path, capsys):
    path = make_snapshot(tmp_path, [
        make_batch("a", [0.1]),
        make_batch("b", [0.2]),
    ])
    main([path, "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    labels = [d["label"] for d in data]
    assert "a" in labels and "b" in labels


def test_main_missing_snapshot_exits(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main(["/no/such/file.json"])
    assert exc_info.value.code == 1


def test_main_label_filter(tmp_path, capsys):
    path = make_snapshot(tmp_path, [
        make_batch("keep", [0.1]),
        make_batch("drop", [0.2]),
    ])
    main([path, "--labels", "keep"])
    out = capsys.readouterr().out
    assert "keep" in out
    assert "drop" not in out
