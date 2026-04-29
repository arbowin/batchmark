"""Tests for batchmark.zip_cli."""

from __future__ import annotations

import json
import os
import sys
import pytest

from batchmark.zip_cli import build_zip_parser, main


def _write_json(tmp_path, name: str, batches):
    path = tmp_path / name
    path.write_text(json.dumps(batches))
    return str(path)


def _sample_left(tmp_path):
    data = [
        {"label": "cmd_a", "runs": [{"elapsed": 1.0, "returncode": 0}]},
        {"label": "cmd_b", "runs": [{"elapsed": 2.0, "returncode": 0}]},
    ]
    return _write_json(tmp_path, "left.json", data)


def _sample_right(tmp_path):
    data = [
        {"label": "cmd_a", "runs": [{"elapsed": 1.5, "returncode": 0}]},
        {"label": "cmd_c", "runs": [{"elapsed": 3.0, "returncode": 0}]},
    ]
    return _write_json(tmp_path, "right.json", data)


def test_build_zip_parser_defaults():
    p = build_zip_parser()
    args = p.parse_args(["l.json", "r.json"])
    assert args.left == "l.json"
    assert args.right == "r.json"
    assert args.left_name == "left"
    assert args.right_name == "right"
    assert args.format == "text"


def test_build_zip_parser_custom_names():
    p = build_zip_parser()
    args = p.parse_args(["l.json", "r.json", "--left-name", "base", "--right-name", "new"])
    assert args.left_name == "base"
    assert args.right_name == "new"


def test_build_zip_parser_json_format():
    p = build_zip_parser()
    args = p.parse_args(["l.json", "r.json", "--format", "json"])
    assert args.format == "json"


def test_main_text_output(tmp_path, capsys):
    left = _sample_left(tmp_path)
    right = _sample_right(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        main([left, right])
    # exits 1 because of unmatched labels
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "cmd_a" in captured.out


def test_main_json_output(tmp_path, capsys):
    left = _sample_left(tmp_path)
    right = _sample_right(tmp_path)
    with pytest.raises(SystemExit):
        main([left, right, "--format", "json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert isinstance(parsed, list)
    labels = [item["label"] for item in parsed]
    assert "cmd_a" in labels


def test_main_exits_zero_when_all_labels_match(tmp_path):
    data = [{"label": "x", "runs": [{"elapsed": 1.0, "returncode": 0}]}]
    left = _write_json(tmp_path, "l.json", data)
    right = _write_json(tmp_path, "r.json", data)
    # Should not raise SystemExit(1)
    main([left, right])  # exits normally (no sys.exit call)
