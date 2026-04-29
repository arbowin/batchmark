"""Tests for batchmark.interpolate_cli."""

from __future__ import annotations

import json
import os
import sys

import pytest

from batchmark.interpolate_cli import build_interpolate_parser, main


def _write_json(tmp_path, data) -> str:
    p = tmp_path / "batches.json"
    p.write_text(json.dumps(data))
    return str(p)


def _sample_data():
    return [
        {
            "label": "alpha",
            "runs": [
                {"elapsed": 1.0, "returncode": 0, "command": "echo", "stdout": "", "stderr": ""},
                {"elapsed": 2.0, "returncode": 0, "command": "echo", "stdout": "", "stderr": ""},
            ],
        },
        {
            "label": "beta",
            "runs": [
                {"elapsed": 3.0, "returncode": 0, "command": "echo", "stdout": "", "stderr": ""},
            ],
        },
    ]


def test_build_interpolate_parser_defaults():
    p = build_interpolate_parser()
    args = p.parse_args(["dummy.json"])
    assert args.target == 10
    assert args.format == "text"


def test_build_interpolate_parser_custom_target():
    p = build_interpolate_parser()
    args = p.parse_args(["dummy.json", "--target", "20"])
    assert args.target == 20


def test_build_interpolate_parser_json_format():
    p = build_interpolate_parser()
    args = p.parse_args(["dummy.json", "--format", "json"])
    assert args.format == "json"


def test_main_text_output_contains_label(tmp_path, capsys):
    path = _write_json(tmp_path, _sample_data())
    main([path, "--target", "4"])
    captured = capsys.readouterr()
    assert "alpha" in captured.out
    assert "beta" in captured.out


def test_main_json_output_is_valid(tmp_path, capsys):
    path = _write_json(tmp_path, _sample_data())
    main([path, "--target", "4", "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == 2


def test_main_json_output_total_equals_target(tmp_path, capsys):
    path = _write_json(tmp_path, _sample_data())
    main([path, "--target", "5", "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    for item in data:
        assert item["total"] == 5


def test_main_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "nonexistent.json"), "--target", "4"])
    assert exc_info.value.code != 0
